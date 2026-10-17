#!/usr/bin/env python3
"""Run the original Suwako 808 update dispatcher with controlled engine services."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))

import pefile
from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_ECX, UC_X86_REG_EIP,
    UC_X86_REG_ESP,
)

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
UPDATE_DISPATCH = 0x007876D0
OBJECT = 0x01000000
STACK = 0x02000000
VTABLE = 0x01100000
STOP = 0x03000000
FLOOR_STUB = STOP + 0x100
FLOOR_VALUE = STOP + 0x200
CREATE_CHILD = STOP + 0x10


class Suwako808Oracle:
    """Execute original dispatch/update code; replace only engine-owned services.

    The stage floor, random generator, collision probe, animation tick, and
    object factory are controlled stubs. The handler, branching, arithmetic,
    custom-data construction, and child-call arguments are original x86.
    """

    def __init__(self, exe: Path):
        raw = exe.read_bytes()
        self.exe_path = exe
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if self.sha256 != REFERENCE_SHA256:
            raise ValueError(f"reference SHA-256 mismatch: {self.sha256}")
        pe = pefile.PE(data=raw)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        image = pe.get_memory_mapped_image()
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(self.base, (len(image) + 0xFFF) & ~0xFFF)
        self.uc.mem_write(self.base, image)
        for address, size in (
            (OBJECT, 0x3000), (STACK, 0x30000), (VTABLE, 0x1000),
            (STOP, 0x1000),
        ):
            self.uc.mem_map(address, size)
        # The floor helper returns its test value in ST(0), as the original
        # x87 ABI requires. Its body is only a controlled environment input.
        self.uc.mem_write(FLOOR_STUB, b"\xd9\x05" + struct.pack("<I", FLOOR_VALUE) + b"\xc3")
        self.uc.mem_write(STOP, b"\xf4")
        self.uc.mem_write(STOP + 0x10, b"\xc2\x04\x00")  # vtable action-resource callback
        self.uc.hook_add(UC_HOOK_CODE, self._hook)
        self.children: list[dict[str, object]] = []
        self.random_draws: list[int] = []
        self.random_values: list[int] = []
        self.floor_y = 500.0
        self.collision = False
        self.constructor_active = False
        self.constructor_entry_sp = 0

    @staticmethod
    def _f32(bits: int) -> float:
        return struct.unpack("<f", struct.pack("<I", bits))[0]

    def _return(self, uc: Uc, esp: int, ret_pop: int = 0) -> None:
        ret = struct.unpack("<I", uc.mem_read(esp, 4))[0]
        uc.reg_write(UC_X86_REG_ESP, esp + 4 + ret_pop)
        uc.reg_write(UC_X86_REG_EIP, ret)

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        if address == STOP:
            uc.emu_stop()
            return
        if address == 0x007996C9 and self.constructor_active:
            # The action-dispatch tail uses EBP as scratch while returning
            # through a jump-table branch. Restore the synthetic caller frame
            # at this final epilogue instruction only.
            frame = self.constructor_entry_sp - 4
            uc.mem_write(frame, struct.pack("<I", 0xDEADBEEF))
            uc.reg_write(UC_X86_REG_EBP, frame)
            return
        esp = uc.reg_read(UC_X86_REG_ESP)
        if address == CREATE_CHILD:
            words = struct.unpack("<8I", uc.mem_read(esp, 32))
            object_id, x, y, facing, arg4, custom, flags = words[1:]
            custom_values = struct.unpack("<3f", uc.mem_read(custom, 12)) if custom else ()
            self.children.append({
                "object_id": object_id,
                "x": self._f32(x),
                "y": self._f32(y),
                "facing": facing,
                "arg4": arg4,
                "custom_data": list(custom_values),
                "flags": flags,
            })
            # Mirrors the factory's stdcall cleanup (ret 0x1c); it does not
            # create an object or run its constructor/update.
            self._return(uc, esp, 0x1C)
            uc.reg_write(UC_X86_REG_EAX, OBJECT + 0x1000 + len(self.children) * 0x400)
        elif address == 0x004099F0:
            bound = struct.unpack("<I", uc.mem_read(esp + 4, 4))[0]
            if not self.random_values:
                raise RuntimeError("deterministic random values exhausted")
            value = self.random_values.pop(0)
            if not 0 <= value < bound:
                raise ValueError(f"random value {value} is outside requested range [0,{bound})")
            self.random_draws.append(bound)
            # This helper is cdecl; the caller removes both bounded-RNG args.
            self._return(uc, esp)
            uc.reg_write(UC_X86_REG_EAX, value)
        elif address in (0x004095F0, 0x00409580):
            angle = struct.unpack("<f", uc.mem_read(esp + 4, 4))[0]
            radians = math.radians(angle if address == 0x004095F0 else angle - 90.0)
            uc.mem_write(FLOOR_VALUE, struct.pack("<f", math.sin(radians)))
            uc.reg_write(UC_X86_REG_EIP, FLOOR_STUB)
        elif address == 0x004397F0:
            uc.mem_write(FLOOR_VALUE, struct.pack("<f", self.floor_y))
            uc.reg_write(UC_X86_REG_EIP, FLOOR_STUB)
        elif address == 0x0048CE90:
            uc.reg_write(UC_X86_REG_EAX, int(self.collision))
            self._return(uc, esp, 12)
        elif address == 0x0048CE30:
            self._return(uc, esp, 4)
        elif address == 0x00438C60:
            uc.reg_write(UC_X86_REG_EAX, 0)
            self._return(uc, esp)

    def initialize_child(
        self, custom_data: tuple[float, float, float], *, sequence: int = 1,
        x: float = 300.0, y: float = 400.0, facing: int = 1,
    ) -> dict[str, object]:
        """Run the original 808 base/action initializer with trig results controlled.

        The action initializer and vector arithmetic execute from the PE. The
        resource virtual is a no-op and the sine service is replaced with the
        matching mathematical value; no asset loading or object factory runs.
        """
        uc = self.uc
        custom = STOP + 0xC00
        uc.mem_write(custom, struct.pack("<3f", *custom_data))
        uc.mem_write(OBJECT, bytes(0x3000))
        uc.mem_write(OBJECT, struct.pack("<I", VTABLE))
        uc.mem_write(VTABLE + 0x0C, struct.pack("<I", STOP + 0x10))
        uc.mem_write(OBJECT + 0x13C, struct.pack("<H", 0x328))
        uc.mem_write(OBJECT + 0x13E, struct.pack("<H", sequence))
        uc.mem_write(OBJECT + 0x35C, struct.pack("<I", custom))
        uc.mem_write(OBJECT + 0x104, struct.pack("<b", facing))
        uc.mem_write(OBJECT + 0xEC, struct.pack("<f", x))
        uc.mem_write(OBJECT + 0xF0, struct.pack("<f", y))
        self.random_values = [0] * 16
        entry_sp = STACK + 0x20000 - 4
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EBP, 0xDEADBEEF)
        uc.reg_write(UC_X86_REG_ECX, OBJECT)
        uc.reg_write(UC_X86_REG_EIP, 0x00799000)
        self.constructor_active = True
        self.constructor_entry_sp = entry_sp
        try:
            uc.emu_start(0x00799000, STOP, count=100000)
        finally:
            self.constructor_active = False
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"808 initializer did not return cleanly: EIP={uc.reg_read(UC_X86_REG_EIP):#x}")
        fields = {}
        for name, offset in (("vx", 0xF4), ("vy", 0xF8), ("scalar_11c", 0x11C),
                             ("scalar_120", 0x120), ("lifetime_12c", 0x12C)):
            fields[name] = struct.unpack("<f", uc.mem_read(OBJECT + offset, 4))[0]
        return {
            "sequence": sequence,
            "custom_data": list(custom_data),
            "initialized": fields,
            "scope": "Original base and action-808 initializers execute; resource vtable callback is a no-op and sine helper results are supplied from math.sin. Asset loading/factory are not executed.",
        }

    def initialize_and_update_child(
        self, custom_data: tuple[float, float, float], *,
        x: float = 300.0, y: float = 400.0, facing: int = 1,
        ticks: int = 4,
    ) -> dict[str, object]:
        """Select the PAT sequence from customData[2], then execute original ticks."""
        sequence = int(custom_data[2])
        if float(sequence) != custom_data[2] or sequence < 0 or sequence > 0xFFFF:
            raise ValueError("custom_data[2] must be an unsigned integral sequence index")
        initialized = self.initialize_child(custom_data, sequence=sequence, x=x, y=y, facing=facing)
        velocity = initialized["initialized"]
        if ticks < 1 or ticks > 120:
            raise ValueError("ticks must be between 1 and 120")
        states = []
        state = {"x": x, "y": y, "vx": float(velocity["vx"]),
                 "vy": float(velocity["vy"]), "scalar_11c": float(velocity["scalar_11c"]),
                 "render_alpha": 0xFF}
        for _ in range(ticks):
            tick = self.run(
                x=float(state["x"]), y=float(state["y"]), facing=facing,
                sequence=1, initial_alpha=int(state["render_alpha"]),
                initial_vx=float(state["vx"]), initial_vy=float(state["vy"]),
                initial_scalar_11c=float(state["scalar_11c"]),
                random_values=(),
            )
            state = tick["parent"]
            states.append({"tick": len(states) + 1, **state})
        return {
            "custom_data": list(custom_data),
            "sequence_source": "custom_data[2], confirmed by Suwako initializer 0x799000 and object-route audit ITERATION34",
            "initializer": initialized,
            "updates": states,
            "final_state": state,
        }

    def split_and_update_children(
        self, *, x: float = 300.0, y: float = 400.0, facing: int = 1,
        ticks: int = 4, floor_y: float = 500.0,
        random_values: tuple[int, ...] = (10, 2, 20, 4),
    ) -> dict[str, object]:
        """Chain the original parent split into initialized candidate child updates."""
        parent = self.run(x=x, y=y, facing=facing, floor_y=floor_y,
                          random_values=random_values)
        children = []
        for child in parent["children"]:
            # Each child gets a fresh CPU/memory image. Reusing Unicorn after
            # constructor dispatch leaves stale state at the stop page.
            child_oracle = Suwako808Oracle(self.exe_path)
            child_run = child_oracle.initialize_and_update_child(
                tuple(child["custom_data"]), x=float(child["x"]),
                y=float(child["y"]), facing=int(child["facing"]), ticks=ticks,
            )
            children.append({"factory_call": child, **child_run})
        return {
            "schema": 1,
            "reference_sha256": self.sha256,
            "parent_split": parent,
            "children": children,
            "scope": "Original parent and child update/initializer handlers execute. The initializer sequence comes from custom_data[2], not factory arg4. Factory, resource callback, stage/collision services and sine-table helpers remain controlled.",
        }

    def run(
        self, *, x: float = 300.0, y: float = 400.0, facing: int = 1,
        floor_y: float = 500.0, collision: bool = False, latch: int = 0,
        sequence: int = 0, initial_alpha: int = 0xFF, initial_vx: float = 0.0,
        initial_vy: float = 0.0, initial_scalar_11c: float = 0.0,
        random_values: tuple[int, ...] = (10, 2, 20, 4),
    ) -> dict[str, object]:
        uc = self.uc
        self.children.clear()
        self.random_draws.clear()
        self.random_values = list(random_values)
        self.floor_y = floor_y
        self.collision = collision
        uc.mem_write(OBJECT, bytes(0x3000))
        uc.mem_write(OBJECT, struct.pack("<I", VTABLE))
        uc.mem_write(VTABLE + 0x44, struct.pack("<I", CREATE_CHILD))
        for offset, value in ((0x13C, 0x328), (0x13E, sequence), (0x36C, latch), (0x190, 0)):
            uc.mem_write(OBJECT + offset, struct.pack("<H", value))
        uc.mem_write(OBJECT + 0x104, struct.pack("<b", facing))
        if not 0 <= initial_alpha <= 0xFF:
            raise ValueError("initial_alpha must be an unsigned byte")
        uc.mem_write(OBJECT + 0x113, struct.pack("<B", initial_alpha))
        for offset, value in ((0xEC, x), (0xF0, y), (0xF4, initial_vx), (0xF8, initial_vy), (0x11C, initial_scalar_11c)):
            uc.mem_write(OBJECT + offset, struct.pack("<f", value))
        entry_sp = STACK + 0x20000 - 4
        uc.mem_write(entry_sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESP, entry_sp)
        uc.reg_write(UC_X86_REG_EBP, 0xDEADBEEF)
        uc.reg_write(UC_X86_REG_ECX, OBJECT)
        uc.reg_write(UC_X86_REG_EIP, UPDATE_DISPATCH)
        uc.emu_start(UPDATE_DISPATCH, STOP, count=100000)
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"update dispatcher did not return cleanly: EIP={uc.reg_read(UC_X86_REG_EIP):#x}")
        return {
            "schema": 1,
            "reference_sha256": self.sha256,
            "action": 0x328,
            "handler_va": "0x00788d3e",
            "input": {"x": x, "y": y, "facing": facing, "floor_y": floor_y,
                      "collision": collision, "latch": latch, "sequence": sequence,
                      "initial_alpha": initial_alpha, "initial_vx": initial_vx, "initial_vy": initial_vy,
                      "random_values": list(random_values)},
            "children": self.children,
            "random_bounds": self.random_draws,
            "parent": {
                "split_latch": struct.unpack("<H", uc.mem_read(OBJECT + 0x36C, 2))[0],
                "x": struct.unpack("<f", uc.mem_read(OBJECT + 0xEC, 4))[0],
                "y": struct.unpack("<f", uc.mem_read(OBJECT + 0xF0, 4))[0],
                "vx": struct.unpack("<f", uc.mem_read(OBJECT + 0xF4, 4))[0],
                "vy": struct.unpack("<f", uc.mem_read(OBJECT + 0xF8, 4))[0],
                "scalar_11c": struct.unpack("<f", uc.mem_read(OBJECT + 0x11C, 4))[0],
                "scalar_120": struct.unpack("<f", uc.mem_read(OBJECT + 0x120, 4))[0],
                "render_alpha": struct.unpack("<B", uc.mem_read(OBJECT + 0x113, 1))[0],
            },
            "scope": "Original action dispatcher and Suwako 808 x86 update execute. Floor, bounded RNG, collision/audio and animation services plus the factory are deterministic stubs; child constructors and later updates are not executed.",
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/x86-suwako-808-update.json")
    parser.add_argument("--floor-y", type=float, default=500.0)
    parser.add_argument("--collision", action="store_true")
    parser.add_argument("--latch", type=int, choices=(0, 1), default=0)
    parser.add_argument("--random-values", type=int, nargs="*", default=(10, 2, 20, 4))
    parser.add_argument("--child-ticks", type=int, default=4)
    parser.add_argument("--chain-children", action="store_true")
    args = parser.parse_args()
    oracle = Suwako808Oracle(args.exe)
    if args.chain_children:
        report = oracle.split_and_update_children(
            floor_y=args.floor_y, ticks=args.child_ticks,
            random_values=tuple(args.random_values),
        )
    else:
        report = oracle.run(
            floor_y=args.floor_y, collision=args.collision, latch=args.latch,
            random_values=tuple(args.random_values),
        )
    report["passed"] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Suwako 808 original update: children={len(report['children'])}; output={args.output}")


if __name__ == "__main__":
    main()
