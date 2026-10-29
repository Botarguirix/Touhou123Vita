"""Translate discovered x86 functions into C for recomp/runtime/guest.h.

One C function per guest function, one statement group per instruction, a
label per instruction. Instructions the lifter does not support become a
`guest_fault` call, so a missing case fails visibly when executed instead of
being skipped. x87 instructions are decoded from their opcode and ModRM bytes:
the Intel/AT&T operand-order confusion around fsub/fsubr and fdiv/fdivr in the
DC/DE forms makes mnemonic-based decoding unsafe.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from capstone import x86_const as X

from recomp.analysis.discover import Discovery, Function

REG32 = {"eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"}
REG16 = {"ax": "eax", "cx": "ecx", "dx": "edx", "bx": "ebx", "sp": "esp", "bp": "ebp",
         "si": "esi", "di": "edi"}
REG8L = {"al": "eax", "cl": "ecx", "dl": "edx", "bl": "ebx"}
REG8H = {"ah": "eax", "ch": "ecx", "dh": "edx", "bh": "ebx"}
CTYPE = {1: "uint8_t", 2: "uint16_t", 4: "uint32_t"}
STYPE = {1: "int8_t", 2: "int16_t", 4: "int32_t"}
BITS = {1: 8, 2: 16, 4: 32}
CONDITIONS = {
    "o": "CC_O", "no": "CC_NO", "b": "CC_B", "c": "CC_B", "nae": "CC_B", "ae": "CC_AE",
    "nb": "CC_AE", "nc": "CC_AE", "e": "CC_E", "z": "CC_E", "ne": "CC_NE", "nz": "CC_NE",
    "be": "CC_BE", "na": "CC_BE", "a": "CC_A", "nbe": "CC_A", "s": "CC_S", "ns": "CC_NS",
    "p": "CC_P", "pe": "CC_P", "np": "CC_NP", "po": "CC_NP", "l": "CC_L", "nge": "CC_L",
    "ge": "CC_GE", "nl": "CC_GE", "le": "CC_LE", "ng": "CC_LE", "g": "CC_G", "nle": "CC_G",
}
ALU = {"add": "add", "adc": "adc", "sub": "sub", "sbb": "sbb"}
LOGIC = {"and": "&", "or": "|", "xor": "^"}
SHIFTS = {"shl": "shl", "sal": "shl", "shr": "shr", "sar": "sar", "rol": "rol", "ror": "ror",
          "rcl": "rcl", "rcr": "rcr"}
SEGMENT_SELECTORS = {"cs": "SEL_CS", "ds": "SEL_DS", "es": "SEL_ES", "ss": "SEL_SS",
                     "fs": "SEL_FS", "gs": "SEL_GS"}
STRING_REP = {"": 0, "rep": 1, "repe": 1, "repz": 1, "repne": 2, "repnz": 2}
BIT_OPS = {"bt": None, "bts": "|", "btr": "& ~", "btc": "^"}
X87_ARITH = ["X87_ADD", "X87_MUL", None, None, "X87_SUB", "X87_SUBR", "X87_DIV", "X87_DIVR"]
# DC/DE register forms swap SUB/SUBR and DIV/DIVR relative to D8.
X87_ARITH_REV = ["X87_ADD", "X87_MUL", None, None, "X87_SUBR", "X87_SUB", "X87_DIVR", "X87_DIV"]


class Unsupported(Exception):
    pass


def _load_natives() -> frozenset[int]:
    """Addresses with a native host replacement: always called through guest_call."""
    path = Path(__file__).resolve().parents[1] / "host/natives.txt"
    if not path.exists():
        return frozenset()
    return frozenset(int(line.split()[0], 16) for line in path.read_text().splitlines()
                     if line.strip() and not line.startswith("#"))


NATIVES = _load_natives()


def fn_name(va: int) -> str:
    return f"f_{va:08x}"


@dataclass
class LiftResult:
    source: str
    functions: list[int]
    faults: dict[int, str] = field(default_factory=dict)  # address -> instruction text
    dead_flags: int = 0  # instructions emitted without their (unread) flags


class Lifter:
    def __init__(self, discovery: Discovery, entries: set[int]):
        self.d = discovery
        self.image = discovery.image
        self.entries = entries
        self.lifted: set[int] = set()
        self.traps: set[int] = set()
        self.eliminate_dead_flags = True

    # -- operands -------------------------------------------------------------------------
    def reg(self, ins, reg_id) -> str:
        name = ins.reg_name(reg_id)
        if name in REG32:
            return f"c->{name}.d"
        if name in REG16:
            return f"c->{REG16[name]}.w"
        if name in REG8L:
            return f"c->{REG8L[name]}.b.l"
        if name in REG8H:
            return f"c->{REG8H[name]}.b.h"
        raise Unsupported(f"register {name}")

    def address(self, ins, op) -> str:
        m = op.mem
        parts = []
        if m.base:
            parts.append(self.reg(ins, m.base))
        if m.index:
            index = self.reg(ins, m.index)
            parts.append(index if m.scale == 1 else f"{index} * {m.scale}u")
        disp = m.disp & 0xFFFFFFFF
        if disp or not parts:
            parts.append(f"0x{disp:x}u")
        expr = " + ".join(parts)
        if m.segment:
            seg = ins.reg_name(m.segment)
            if seg == "fs":
                expr = f"c->fs_base + {expr}"
            elif seg not in ("ds", "ss", "es", "cs"):
                raise Unsupported(f"segment {seg}")
        return f"(uint32_t)({expr})"

    def read(self, ins, op, size=None) -> str:
        size = size or op.size
        if op.type == X.X86_OP_REG:
            return self.reg(ins, op.reg)
        if op.type == X.X86_OP_IMM:
            return f"({CTYPE[size]})0x{op.imm & ((1 << (8 * size)) - 1):x}u"
        if op.type == X.X86_OP_MEM:
            if size not in (1, 2, 4):
                raise Unsupported(f"memory read of {size} bytes")
            return f"rd{BITS[size]}({self.address(ins, op)})"
        raise Unsupported("operand type")

    def write(self, ins, op, value: str) -> str:
        if op.type == X.X86_OP_REG:
            return f"{self.reg(ins, op.reg)} = {value};"
        if op.type == X.X86_OP_MEM:
            if op.size not in (1, 2, 4):
                raise Unsupported(f"memory write of {op.size} bytes")
            return f"wr{BITS[op.size]}({self.address(ins, op)}, {value});"
        raise Unsupported("write to non-lvalue")

    def rmw(self, ins, op, body) -> str:
        """Read-modify-write with the memory address evaluated once. body(x) -> C expr."""
        t = CTYPE[op.size]
        if op.type == X.X86_OP_MEM:
            n = BITS[op.size]
            return (f"{{ uint32_t ea = {self.address(ins, op)}; {t} x = rd{n}(ea); "
                    f"wr{n}(ea, {body('x')}); }}")
        r = self.reg(ins, op.reg)
        return f"{{ {t} x = {r}; {r} = {body('x')}; }}"

    # -- control flow helpers ---------------------------------------------------------------
    def call_expr(self, target: int) -> str:
        if target in self.lifted and target not in NATIVES:
            return f"{fn_name(target)}(c);"
        return f"guest_call(c, 0x{target:08x}u);"

    def branch(self, fn: Function, target: int) -> str:
        if target in fn.insns:
            return f"goto L_{target:08x};"
        return f"{{ {self.call_expr(target)} return; }}"  # tail call into another function

    # -- instructions ------------------------------------------------------------------------
    def lift_insn(self, fn: Function, ins) -> str:
        m = ins.mnemonic
        ops = ins.operands
        nxt = ins.address + ins.size
        words = m.split()
        prefix = words[0] if len(words) > 1 else ""
        base = words[-1]

        if base in ("wait", "nop"):
            return ";"
        if base in ("int3", "hlt", "ud2"):
            # A trap in the original as well: kept as a visible fault, not counted as
            # an unsupported instruction.
            self.traps.add(ins.address)
            return f'guest_fault(c, 0x{ins.address:08x}u, "{base} executed");'
        k = self._opcode_offset(ins)
        if k + 1 < len(ins.bytes) and 0xD8 <= ins.bytes[k] <= 0xDF:
            return self.lift_x87(ins)
        if base == "mov":
            if ops[1].type == X.X86_OP_REG and ins.reg_name(ops[1].reg) in SEGMENT_SELECTORS:
                return self.write(ins, ops[0], f"(uint16_t){SEGMENT_SELECTORS[ins.reg_name(ops[1].reg)]}")
            return self.write(ins, ops[0], self.read(ins, ops[1], ops[0].size))
        if base in ("movzx", "movsx"):
            src = self.read(ins, ops[1])
            if base == "movsx":
                src = f"({CTYPE[ops[0].size]})({STYPE[ops[0].size]})({STYPE[ops[1].size]}){src}"
            else:
                src = f"({CTYPE[ops[0].size]}){src}"
            return self.write(ins, ops[0], src)
        if base == "lea":
            return self.write(ins, ops[0], f"({CTYPE[ops[0].size]}){self.address(ins, ops[1])}")
        if base in ALU:
            n = BITS[ops[0].size]
            src = self.read(ins, ops[1], ops[0].size)
            return self.rmw(ins, ops[0], lambda x: f"op_{ALU[base]}{n}(c, {x}, {src})")
        if base in LOGIC:
            n, t = BITS[ops[0].size], CTYPE[ops[0].size]
            src = self.read(ins, ops[1], ops[0].size)
            if ops[0].type == X.X86_OP_MEM:
                return (f"{{ uint32_t ea = {self.address(ins, ops[0])}; {t} r = ({t})(rd{n}(ea) "
                        f"{LOGIC[base]} {src}); wr{n}(ea, r); flags_logic{n}(c, r); }}")
            r = self.reg(ins, ops[0].reg)
            return f"{{ {t} v = {src}; {r} = ({t})({r} {LOGIC[base]} v); flags_logic{n}(c, {r}); }}"
        if base == "cmp":
            n = BITS[ops[0].size]
            return f"(void)op_sub{n}(c, {self.read(ins, ops[0])}, {self.read(ins, ops[1], ops[0].size)});"
        if base == "test":
            n, t = BITS[ops[0].size], CTYPE[ops[0].size]
            return f"flags_logic{n}(c, ({t})({self.read(ins, ops[0])} & {self.read(ins, ops[1], ops[0].size)}));"
        if base in ("inc", "dec", "neg"):
            n = BITS[ops[0].size]
            return self.rmw(ins, ops[0], lambda x: f"op_{base}{n}(c, {x})")
        if base == "not":
            t = CTYPE[ops[0].size]
            return self.rmw(ins, ops[0], lambda x: f"({t})~{x}")
        if base in SHIFTS:
            n = BITS[ops[0].size]
            count = "1" if len(ops) == 1 else self.read(ins, ops[1], 1)
            return self.rmw(ins, ops[0], lambda x: f"op_{SHIFTS[base]}{n}(c, {x}, (uint8_t){count})")
        if base in ("shld", "shrd"):
            if ops[0].size != 4:
                raise Unsupported(f"{base} of 16 bits")
            src = self.read(ins, ops[1])
            count = self.read(ins, ops[2], 1)
            return self.rmw(ins, ops[0], lambda x: f"op_{base}32(c, {x}, {src}, (uint8_t){count})")
        if base in BIT_OPS:
            return self.lift_bit_op(ins, base)
        if base == "xadd":
            if ops[0].size != 4:
                raise Unsupported("xadd of 8/16 bits")
            src = self.reg(ins, ops[1].reg)
            if ops[0].type == X.X86_OP_MEM:
                return f"{{ uint32_t ea = {self.address(ins, ops[0])}; {src} = op_xadd32_mem(c, ea, {src}); }}"
            dst = self.reg(ins, ops[0].reg)
            return f"{{ uint32_t a = {dst}, b = {src}; {dst} = op_add32(c, a, b); {src} = a; }}"
        if base == "xlatb":
            return "c->eax.b.l = rd8(c->ebx.d + c->eax.b.l);"
        if base == "pushfd":
            return "push32(c, get_eflags(c));"
        if base == "popfd":
            return "set_eflags(c, pop32(c));"
        if base == "cpuid":
            return "op_cpuid(c);"
        if base == "imul":
            if len(ops) == 1:
                if ops[0].size == 1:
                    return f"op_imul1_8(c, {self.read(ins, ops[0])});"
                if ops[0].size != 4:
                    raise Unsupported("imul r/m16")
                return f"op_imul1_32(c, {self.read(ins, ops[0])});"
            n = BITS[ops[0].size]
            a = self.read(ins, ops[0]) if len(ops) == 2 else self.read(ins, ops[1])
            b = self.read(ins, ops[1]) if len(ops) == 2 else self.read(ins, ops[2], ops[0].size)
            return self.write(ins, ops[0], f"op_imul{n}(c, {a}, {b})")
        if base in ("mul", "div", "idiv"):
            if ops[0].size != 4:
                raise Unsupported(f"{base} r/m8/16")
            if base == "mul":
                return f"op_mul1_32(c, {self.read(ins, ops[0])});"
            return f"op_{base}1_32(c, {self.read(ins, ops[0])}, 0x{ins.address:08x}u);"
        if base == "cdq":
            return "c->edx.d = (uint32_t)((int32_t)c->eax.d >> 31);"
        if base == "cwde":
            return "c->eax.d = (uint32_t)(int32_t)(int16_t)c->eax.w;"
        if base == "cbw":
            return "c->eax.w = (uint16_t)(int16_t)(int8_t)c->eax.b.l;"
        if base == "push":
            if ops[0].type == X.X86_OP_IMM:
                return f"push32(c, 0x{ops[0].imm & 0xFFFFFFFF:x}u);"
            if ops[0].size != 4:
                raise Unsupported("push of 16 bits")
            return f"{{ uint32_t v = {self.read(ins, ops[0])}; push32(c, v); }}"
        if base == "pop":
            if ops[0].size != 4:
                raise Unsupported("pop of 16 bits")
            return f"{{ uint32_t v = pop32(c); {self.write(ins, ops[0], 'v')} }}"
        if base == "xchg":
            t = CTYPE[ops[0].size]
            return (f"{{ {t} a = {self.read(ins, ops[0])}; {t} b = {self.read(ins, ops[1])}; "
                    f"{self.write(ins, ops[0], 'b')} {self.write(ins, ops[1], 'a')} }}")
        if base == "leave":
            return "c->esp.d = c->ebp.d; c->ebp.d = pop32(c);"
        if base == "sahf":
            return "op_sahf(c);"
        if base == "cld":
            return "c->df = 0;"
        if base == "std":
            return "c->df = 1;"
        if base.startswith("set") and base[3:] in CONDITIONS:
            return self.write(ins, ops[0], f"(uint8_t){CONDITIONS[base[3:]]}(c)")
        if base.startswith("cmov") and base[4:] in CONDITIONS:
            return f"if ({CONDITIONS[base[4:]]}(c)) {{ {self.write(ins, ops[0], self.read(ins, ops[1]))} }}"
        if base in ("movsb", "movsw", "movsd", "stosb", "stosw", "stosd") and prefix in ("", "rep"):
            size = {"b": 1, "w": 2, "d": 4}[base[-1]]
            kind = "movs" if base.startswith("movs") else "stos"
            return f"op_rep_{kind}(c, {size}, {int(prefix == 'rep')}, 0x{ins.address:08x}u);"
        if base in ("scasb", "scasw", "scasd", "cmpsb", "cmpsw", "cmpsd") and prefix in STRING_REP:
            size = {"b": 1, "w": 2, "d": 4}[base[-1]]
            return f"op_{base[:4]}(c, {size}, {STRING_REP[prefix]}, 0x{ins.address:08x}u);"
        if base == "ret":
            pop = ops[0].imm if ops else 0
            return f"c->esp.d += {4 + pop}u; return;"
        if base == "jmp":
            return self.lift_jmp(fn, ins)
        if base.startswith("j") and base[1:] in CONDITIONS:
            return f"if ({CONDITIONS[base[1:]]}(c)) {self.branch(fn, ops[0].imm & 0xFFFFFFFF)}"
        if base == "jecxz":
            return f"if (c->ecx.d == 0) {self.branch(fn, ops[0].imm & 0xFFFFFFFF)}"
        if base == "call":
            return self.lift_call(ins, nxt)
        raise Unsupported(m)

    def lift_bit_op(self, ins, base: str) -> str:
        """bt/bts/btr/btc r/m32, r32|imm8. A register offset on a memory operand
        addresses a bit string, so it can move the effective address."""
        dst, off = ins.operands
        if dst.size != 4:
            raise Unsupported(f"{base} of 16 bits")
        op = BIT_OPS[base]
        if dst.type == X.X86_OP_MEM:
            ea = self.address(ins, dst)
            if off.type == X.X86_OP_REG:
                addr, bit = f"bt_address({ea}, o)", "(o & 31u)"
                head = f"uint32_t o = {self.reg(ins, off.reg)}; uint32_t a = {addr};"
            else:
                bit = f"{off.imm & 31}u"
                head = f"uint32_t a = {ea};"
            body = f"{{ {head} uint32_t v = rd32(a); c->cf = (v >> {bit}) & 1;"
            if op:
                body += f" wr32(a, v {op} (1u << {bit}));"
            return body + " }"
        reg = self.reg(ins, dst.reg)
        bit = f"({self.read(ins, off, 4)} & 31u)" if off.type == X.X86_OP_REG else f"{off.imm & 31}u"
        body = f"{{ uint32_t b = {bit}; c->cf = ({reg} >> b) & 1;"
        if op:
            body += f" {reg} = {reg} {op} (1u << b);"
        return body + " }"

    @staticmethod
    def _opcode_offset(ins) -> int:
        i = 0
        while i < len(ins.bytes) - 1 and ins.bytes[i] in (
                0x66, 0x67, 0xF2, 0xF3, 0xF0, 0x2E, 0x36, 0x3E, 0x26, 0x64, 0x65, 0x9B):
            i += 1
        return i

    def lift_call(self, ins, nxt: int) -> str:
        op = ins.operands[0]
        if op.type == X.X86_OP_IMM:
            target = op.imm & 0xFFFFFFFF
            return f"push32(c, 0x{nxt:08x}u); {self.call_expr(target)}"
        if op.type == X.X86_OP_MEM and not op.mem.base and not op.mem.index:
            slot = op.mem.disp & 0xFFFFFFFF
            if slot in self.image.imports:
                return f"push32(c, 0x{nxt:08x}u); guest_call_import(c, 0x{slot:08x}u);"
        target = self.read(ins, op, 4)
        return f"{{ uint32_t t = {target}; push32(c, 0x{nxt:08x}u); guest_call(c, t); }}"

    def lift_jmp(self, fn: Function, ins) -> str:
        op = ins.operands[0]
        if op.type == X.X86_OP_IMM:
            return self.branch(fn, op.imm & 0xFFFFFFFF)
        switch = next((s for s in fn.switches if s.site == ins.address), None)
        if switch is not None:
            # The jump goes to whatever the original table holds; only targets that
            # discovery followed have labels. For a bounded table that is all of them;
            # for a heuristic one, an unexpected entry fails visibly instead of jumping.
            index = self.reg(ins, op.mem.index)
            cases = " ".join(f"case 0x{t:08x}u: goto L_{t:08x};" for t in sorted(set(switch.targets))
                             if t in fn.insns)
            reason = "switch target outside table" if switch.bound not in ("heuristic", "pending") \
                else f"switch target not discovered ({switch.bound} bound)"
            return (f"switch (rd32(0x{op.mem.disp & 0xFFFFFFFF:x}u + {index} * 4u)) {{ {cases} "
                    f"default: guest_fault(c, 0x{ins.address:08x}u, \"{reason}\"); }}")
        if op.type == X.X86_OP_MEM and not op.mem.base and not op.mem.index:
            slot = op.mem.disp & 0xFFFFFFFF
            if slot in self.image.imports:
                return f"guest_call_import(c, 0x{slot:08x}u); return;"
        return f"{{ uint32_t t = {self.read(ins, op, 4)}; guest_call(c, t); return; }}"

    # -- x87 -----------------------------------------------------------------------------------
    def lift_x87(self, ins) -> str:
        k = self._opcode_offset(ins)
        op, modrm = ins.bytes[k], ins.bytes[k + 1]
        mod, reg, rm = modrm >> 6, (modrm >> 3) & 7, modrm & 7
        mem = next((o for o in ins.operands if o.type == X.X86_OP_MEM), None)
        ea = self.address(ins, mem) if mem is not None else None
        if mod != 3:
            return self._x87_mem(ins, op, reg, ea)
        return self._x87_reg(ins, op, reg, rm)

    def _x87_mem(self, ins, op, reg, ea) -> str:
        if op in (0xD8, 0xDC, 0xDA, 0xDE):
            src = {0xD8: f"x87_m32({ea})", 0xDC: f"x87_m64({ea})",
                   0xDA: f"(x87_t)(int32_t)rd32({ea})", 0xDE: f"(x87_t)(int16_t)rd16({ea})"}[op]
            if reg in (2, 3):  # fcom / fcomp (and ficom / ficomp)
                return f"x87_compare(c, {src}, {reg - 2}, 0);"
            return f"x87_arith(c, {X87_ARITH[reg]}, 0, {src}, 0);"
        table = {
            (0xD9, 4): f"x87_fldenv(c, {ea});", (0xD9, 6): f"x87_fnstenv(c, {ea});",
            (0xDD, 4): f"x87_frstor(c, {ea});", (0xDD, 6): f"x87_fnsave(c, {ea});",
            (0xD9, 0): f"x87_fld_m32(c, {ea});", (0xD9, 2): f"x87_fst_m32(c, {ea}, 0);",
            (0xD9, 3): f"x87_fst_m32(c, {ea}, 1);", (0xD9, 5): f"x87_set_cw(c, rd16({ea}));",
            (0xD9, 7): f"wr16({ea}, x87_get_cw(c));",
            (0xDB, 0): f"x87_fild(c, (int32_t)rd32({ea}));", (0xDB, 1): f"x87_fist(c, {ea}, 4, 1, 1);",
            (0xDB, 2): f"x87_fist(c, {ea}, 4, 0, 0);", (0xDB, 3): f"x87_fist(c, {ea}, 4, 1, 0);",
            (0xDB, 5): f"x87_fld_m80(c, {ea});", (0xDB, 7): f"x87_fst_m80(c, {ea}, 1);",
            (0xDD, 0): f"x87_fld_m64(c, {ea});", (0xDD, 1): f"x87_fist(c, {ea}, 8, 1, 1);",
            (0xDD, 2): f"x87_fst_m64(c, {ea}, 0);", (0xDD, 3): f"x87_fst_m64(c, {ea}, 1);",
            (0xDD, 7): f"wr16({ea}, x87_get_sw(c));",
            (0xDF, 0): f"x87_fild(c, (int16_t)rd16({ea}));", (0xDF, 1): f"x87_fist(c, {ea}, 2, 1, 1);",
            (0xDF, 2): f"x87_fist(c, {ea}, 2, 0, 0);", (0xDF, 3): f"x87_fist(c, {ea}, 2, 1, 0);",
            (0xDF, 5): f"x87_fild(c, (int64_t)rd64({ea}));", (0xDF, 7): f"x87_fist(c, {ea}, 8, 1, 0);",
        }
        if (op, reg) in table:
            return table[(op, reg)]
        raise Unsupported(f"x87 {op:02X} /{reg} memory")

    def _x87_reg(self, ins, op, reg, rm) -> str:
        if op == 0xD8:
            if reg in (2, 3):
                return f"x87_compare(c, x87_st(c, {rm}), {reg - 2}, 0);"
            return f"x87_arith(c, {X87_ARITH[reg]}, 0, x87_st(c, {rm}), 0);"
        if op in (0xDC, 0xDE):
            pop = int(op == 0xDE)
            if op == 0xDE and reg == 3 and rm == 1:
                return "x87_compare(c, x87_st(c, 1), 2, 0);"  # fcompp
            if reg in (2, 3):
                return f"x87_compare(c, x87_st(c, {rm}), {reg - 2 + pop}, 0);"
            return f"x87_arith(c, {X87_ARITH_REV[reg]}, {rm}, x87_st(c, 0), {pop});"
        if op == 0xD9:
            if reg == 0:
                return f"x87_fld_st(c, {rm});"
            if reg == 1:
                return f"x87_fxch(c, {rm});"
            if reg == 2 and rm == 0:
                return ";"  # fnop
            fixed = {(4, 0): "x87_unary(c, 0);", (4, 1): "x87_unary(c, 1);", (4, 4): "x87_unary(c, 6);",
                     (4, 5): "x87_unary(c, 7);", (5, 0): "x87_fld_const(c, 1);",
                     (5, 1): "x87_fld_const(c, 4);", (5, 2): "x87_fld_const(c, 3);",
                     (5, 3): "x87_fld_const(c, 2);", (5, 4): "x87_fld_const(c, 5);",
                     (5, 5): "x87_fld_const(c, 6);", (5, 6): "x87_fld_const(c, 0);",
                     (6, 0): "x87_binary_special(c, 4);", (6, 1): "x87_binary_special(c, 1);",
                     (6, 2): "x87_binary_special(c, 5);", (6, 3): "x87_binary_special(c, 0);",
                     (7, 0): "x87_binary_special(c, 3);", (6, 5): "x87_binary_special(c, 6);",
                     (7, 2): "x87_unary(c, 2);",
                     (7, 4): "x87_unary(c, 3);", (7, 5): "x87_binary_special(c, 2);",
                     (7, 6): "x87_unary(c, 4);", (7, 7): "x87_unary(c, 5);"}
            if (reg, rm) in fixed:
                return fixed[(reg, rm)]
        if op == 0xDA and reg == 5 and rm == 1:
            return "x87_compare(c, x87_st(c, 1), 2, 1);"  # fucompp
        if op == 0xDB:
            if reg == 4 and rm == 3:
                return "x87_reset(c);"   # fninit
            if reg == 4 and rm == 2:
                return "c->fpu.sw &= 0x7F00;"  # fnclex
            if reg in (5, 6):
                return f"x87_comi(c, {rm}, 0);"
        if op == 0xDD:
            if reg == 2:
                return f"x87_fst_st(c, {rm}, 0);"
            if reg == 3:
                return f"x87_fst_st(c, {rm}, 1);"
            if reg in (4, 5):
                return f"x87_compare(c, x87_st(c, {rm}), {reg - 4}, 1);"
            if reg == 0:
                return f"c->fpu.tag_empty |= (uint8_t)(1u << ((c->fpu.top + {rm}) & 7));"
        if op == 0xDF:
            if reg == 4 and rm == 0:
                return "c->eax.w = x87_get_sw(c);"
            if reg in (5, 6):
                return f"x87_comi(c, {rm}, 1);"
        raise Unsupported(f"x87 {op:02X} {0xC0 | reg << 3 | rm:02X}")

    # -- flag liveness ---------------------------------------------------------------------------
    # Arithmetic writes CF ZF SF OF PF into the Cpu on every instruction, and the C
    # compiler cannot drop those stores (Cpu is memory and calls are everywhere).
    # Within a function, flags that no later instruction reads are dead: such add/sub,
    # logic, inc/dec, cmp and test are emitted without flags. Conservative edges: at
    # ret, indirect jumps, tail calls and unresolved jumps every flag is live; a call
    # clobbers them; a shift/rotate by cl may leave them unchanged, so it kills none.
    FLAG_BITS = {
        "cf": (X.X86_EFLAGS_MODIFY_CF | X.X86_EFLAGS_RESET_CF | X.X86_EFLAGS_SET_CF | X.X86_EFLAGS_UNDEFINED_CF,
               X.X86_EFLAGS_TEST_CF),
        "zf": (X.X86_EFLAGS_MODIFY_ZF | X.X86_EFLAGS_RESET_ZF | X.X86_EFLAGS_SET_ZF | X.X86_EFLAGS_UNDEFINED_ZF,
               X.X86_EFLAGS_TEST_ZF),
        "sf": (X.X86_EFLAGS_MODIFY_SF | X.X86_EFLAGS_RESET_SF | X.X86_EFLAGS_SET_SF | X.X86_EFLAGS_UNDEFINED_SF,
               X.X86_EFLAGS_TEST_SF),
        "of": (X.X86_EFLAGS_MODIFY_OF | X.X86_EFLAGS_RESET_OF | X.X86_EFLAGS_SET_OF | X.X86_EFLAGS_UNDEFINED_OF,
               X.X86_EFLAGS_TEST_OF),
        "pf": (X.X86_EFLAGS_MODIFY_PF | X.X86_EFLAGS_RESET_PF | X.X86_EFLAGS_SET_PF | X.X86_EFLAGS_UNDEFINED_PF,
               X.X86_EFLAGS_TEST_PF),
    }
    ALL_FLAGS = frozenset(FLAG_BITS)
    READS_ALL = ("pushfd", "pushf", "lahf")
    SIMPLE_DEAD = ("add", "sub", "and", "or", "xor", "cmp", "test", "inc", "dec")

    def flag_effects(self, ins) -> tuple[frozenset, frozenset]:
        """(read, killed) flag sets of one instruction."""
        base = ins.mnemonic.split()[-1]
        if base in self.READS_ALL:
            return self.ALL_FLAGS, frozenset()
        # Capstone does not report these reads (checked): rcl/rcr/cmc/salc read CF and
        # into reads OF. Missing rcl/rcr cost a crash in the CRT's 64-bit arithmetic.
        extra = {"rcl": {"cf"}, "rcr": {"cf"}, "cmc": {"cf"}, "salc": {"cf"}, "into": {"of"},
                 "daa": {"cf"}, "das": {"cf"}, "aaa": {"cf"}, "aas": {"cf"}}.get(base, set())
        if ins.group(X.X86_GRP_CALL):
            return frozenset(), self.ALL_FLAGS
        if any(op.type == X.X86_OP_REG and ins.reg_name(op.reg).startswith("xmm") for op in ins.operands):
            # SSE: Capstone reports cmpltsd & co. as EFLAGS writers; only the comis family is.
            if base in ("comisd", "comiss", "ucomisd", "ucomiss"):
                return frozenset(), self.ALL_FLAGS
            return frozenset(), frozenset()
        if ins.group(X.X86_GRP_FPU) or base.startswith("f"):
            # Capstone's eflags shares a union with fpu_flags for x87 instructions, so it
            # cannot be trusted there (fchs looked like an EFLAGS writer and killed a cmp;
            # some fstp/fldl2e are not even in the FPU group and claimed to write CF).
            if base.startswith("fcmov"):
                return self.ALL_FLAGS, frozenset()
            if base in ("fcomi", "fcomip", "fucomi", "fucomip"):
                return frozenset(), self.ALL_FLAGS
            return frozenset(), frozenset()
        eflags = getattr(ins, "eflags", 0) or 0
        read = frozenset(f for f, (_, test) in self.FLAG_BITS.items() if eflags & test) | extra
        kill = frozenset(f for f, (mod, _) in self.FLAG_BITS.items() if eflags & mod)
        if base in SHIFTS or base in ("shld", "shrd"):
            if any(op.type == X.X86_OP_REG for op in ins.operands[1:]) or \
               (len(ins.operands) > 1 and ins.operands[-1].type == X.X86_OP_IMM and ins.operands[-1].imm & 31 == 0):
                kill = frozenset()
        return read, kill

    def dead_flag_insns(self, fn: Function) -> set:
        """Addresses whose written flags are never read (see above)."""
        info, succ, live_out_all = {}, {}, set()
        for va in fn.insns:
            ins = self.d._decode_detail(va)
            info[va] = (ins, *self.flag_effects(ins))
            base = ins.mnemonic.split()[-1]
            nxt = va + ins.size
            s = []
            terminal = base in ("ret", "retf", "iretd") or base.startswith(("int3", "hlt", "ud2"))
            if base == "jmp" or ins.group(X.X86_GRP_JUMP):
                op = ins.operands[0] if ins.operands else None
                if op is not None and op.type == X.X86_OP_IMM and op.imm in fn.insns:
                    s.append(op.imm)
                else:
                    live_out_all.add(va)  # indirect, table or tail call
                if base != "jmp":
                    s.append(nxt)
            elif not terminal:
                s.append(nxt)
            if terminal or va in fn.dynamic_tailcalls or va in fn.unresolved_jumps:
                live_out_all.add(va)
            for t in s:
                if t not in fn.insns:
                    live_out_all.add(va)
            succ[va] = [t for t in s if t in fn.insns]
        live_in = {va: frozenset() for va in fn.insns}
        changed = True
        while changed:
            changed = False
            for va in sorted(fn.insns, reverse=True):
                ins, read, kill = info[va]
                out = self.ALL_FLAGS if va in live_out_all else frozenset().union(*(live_in[t] for t in succ[va]))
                new = read | (out - kill)
                if new != live_in[va]:
                    live_in[va] = new
                    changed = True
        dead = set()
        for va, (ins, read, kill) in info.items():
            if ins.mnemonic.split()[-1] not in self.SIMPLE_DEAD or len(ins.mnemonic.split()) > 1:
                continue
            out = self.ALL_FLAGS if va in live_out_all else frozenset().union(*(live_in[t] for t in succ[va]))
            if kill and not (out & kill):
                dead.add(va)
        return dead

    @staticmethod
    def dead_flags_applies(entry: int) -> bool:
        """T123_DEAD_FLAGS_RANGE=lo-hi (hex) limits the pass to those functions (bisecting)."""
        spec = os.environ.get("T123_DEAD_FLAGS_RANGE")
        if not spec:
            return True
        lo, hi = (int(v, 16) for v in spec.split("-"))
        return lo <= entry < hi

    def lift_plain(self, ins) -> str:
        """The instruction without its flags (it is in dead_flag_insns)."""
        base, ops = ins.mnemonic.split()[-1], ins.operands
        t = CTYPE[ops[0].size]
        if base in ("cmp", "test"):
            return ";"
        if base in ("inc", "dec"):
            return self.rmw(ins, ops[0], lambda x: f"({t})({x} {'+' if base == 'inc' else '-'} 1u)")
        op = {"add": "+", "sub": "-", "and": "&", "or": "|", "xor": "^"}[base]
        src = self.read(ins, ops[1], ops[0].size)
        return self.rmw(ins, ops[0], lambda x: f"({t})({x} {op} {src})")

    # -- functions ---------------------------------------------------------------------------
    def lift_function(self, fn: Function, result: LiftResult) -> str:
        lines = [f"void {fn_name(fn.entry)}(Cpu *c) {{", f"    T123_ENTER(0x{fn.entry:08x}u);"]
        if fn.entry not in fn.insns:
            lines.append(f"    guest_fault(c, 0x{fn.entry:08x}u, \"entry does not decode\");")
        addresses = sorted(fn.insns)
        lines.append(f"    goto L_{fn.entry:08x};")
        dead = self.dead_flag_insns(fn) if self.eliminate_dead_flags and self.dead_flags_applies(fn.entry) else set()
        result.dead_flags += len(dead)
        for i, va in enumerate(addresses):
            ins = self.d._decode_detail(va)
            text = f"{ins.mnemonic} {ins.op_str}".strip()
            try:
                body = self.lift_plain(ins) if va in dead else self.lift_insn(fn, ins)
            except Unsupported as exc:
                result.faults[va] = f"{text} ({exc})"
                body = f'guest_fault(c, 0x{va:08x}u, "unsupported: {text}");'
            lines.append(f"L_{va:08x}: /* {text} */")
            lines.append(f"    {body}")
            nxt = va + ins.size
            following = addresses[i + 1] if i + 1 < len(addresses) else None
            kind = self.d.cache[va].kind if va in self.d.cache else None
            terminal = ins.mnemonic in ("ret", "jmp") or ins.mnemonic.startswith(("int3", "hlt", "ud2"))
            ends_flow = terminal or va in fn.dynamic_tailcalls or va in fn.unresolved_jumps
            if not ends_flow and following != nxt:
                if nxt in fn.insns:
                    lines.append(f"    goto L_{nxt:08x};")
                elif nxt in fn.tailcalls or nxt in self.entries:
                    lines.append(f"    {{ {self.call_expr(nxt)} return; }}")
                else:
                    lines.append(f'    guest_fault(c, 0x{nxt:08x}u, "fell off decoded code");')
        lines.append("}")
        return "\n".join(lines)

    PREAMBLE = [
        "/* Generated by recomp/lift from the user's th123.exe. Do not commit. */",
        '#include "guest.h"',
        "#pragma GCC diagnostic ignored \"-Wunused-label\"",
        "",
    ]

    @staticmethod
    def table_source(entries: list[int]) -> list[str]:
        table = ["", "const GuestEntry t123_lifted[] = {"]
        table += [f"    {{0x{e:08x}u, {fn_name(e)}}}," for e in sorted(entries)]
        table += ["};", f"const unsigned t123_lifted_count = {len(entries)};", ""]
        return table

    def lift(self, entries: list[int]) -> LiftResult:
        """Single translation unit (small batches and tests)."""
        self.lifted = set(entries)
        result = LiftResult("", sorted(entries))
        bodies = []
        for entry in sorted(entries):
            fn = self.d.explore(entry, "call", self.entries)
            bodies.append(self.lift_function(fn, result))
        header = self.PREAMBLE + [f"void {fn_name(e)}(Cpu *c);" for e in sorted(entries)]
        result.source = "\n".join(header + [""] + bodies + self.table_source(entries))
        return result

    def lift_units(self, entries: list[int], unit_bytes: int = 1_000_000,
                   progress=None) -> tuple[dict[str, str], LiftResult]:
        """Whole-program output: lifted.h with every prototype, unit_NNN.c files of
        about unit_bytes of C each, and table.c with the dispatch table."""
        self.lifted = set(entries)
        result = LiftResult("", sorted(entries))
        files: dict[str, str] = {}
        prototypes = [f"void {fn_name(e)}(Cpu *c);" for e in sorted(entries)]
        files["lifted.h"] = "\n".join(["#ifndef T123_LIFTED_H", "#define T123_LIFTED_H",
                                       '#include "guest.h"', *prototypes, "#endif", ""])
        unit: list[str] = []
        size = 0

        def flush():
            nonlocal unit, size
            if unit:
                name = f"unit_{len(files) - 1:03d}.c"
                files[name] = "\n".join(self.PREAMBLE + ['#include "lifted.h"', ""] + unit + [""])
                unit, size = [], 0

        for i, entry in enumerate(sorted(entries)):
            fn = self.d.explore(entry, "call", self.entries)
            body = self.lift_function(fn, result)
            unit.append(body)
            size += len(body)
            if size >= unit_bytes:
                flush()
            if progress and i % 500 == 0:
                progress(i, len(entries))
        flush()
        files["table.c"] = "\n".join(['#include "lifted.h"'] + self.table_source(entries))
        return files, result
