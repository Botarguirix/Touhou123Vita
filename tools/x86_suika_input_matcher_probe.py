#!/usr/bin/env python3
"""Run original Player input updates and motion matcher over an ABI-valid deque."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "local/python-deps"))

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"


def run() -> dict[str, object]:
    import pefile
    from unicorn import (Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_HOOK_MEM_INVALID,
                         UC_MODE_32)
    from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_ECX,
                                   UC_X86_REG_EBX, UC_X86_REG_EDI,
                                   UC_X86_REG_EIP, UC_X86_REG_ESI,
                                   UC_X86_REG_ESP)

    exe = ROOT / "original/th123.exe"
    raw = exe.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != REFERENCE_SHA256:
        raise ValueError(f"reference PE SHA-256 mismatch: {digest}")
    pe = pefile.PE(data=raw)
    image = pe.get_memory_mapped_image()
    base = pe.OPTIONAL_HEADER.ImageBase
    image_size = (len(image) + 0xFFF) & ~0xFFF
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(base, image_size)
    uc.mem_write(base, image)

    player, vtable = 0x01000000, 0x01100000
    key_manager, keymap, keymap_vtable = 0x01200000, 0x01300000, 0x01400000
    deque_table, ring_data = 0x01500000, 0x01600000
    player_info, action_node = 0x01700000, 0x01800000
    stack, stop = 0x02000000, 0x03000000
    for address, size in ((player, 0x1000), (vtable, 0x1000),
                          (key_manager, 0x1000), (keymap, 0x1000),
                          (keymap_vtable, 0x1000), (deque_table, 0x1000),
                          (player_info, 0x1000), (action_node, 0x1000),
                          (ring_data, 12 * 0x1000), (stack, 0x10000),
                          (stop, 0x1000)):
        if address < base or address + size > base + image_size:
            uc.mem_map(address, size)
    uc.mem_write(stop, b"\xf4")

    # SokuLib Deque<unsigned short>: proxy, T**, blockCount, offset, size.
    # At 90 words, 12 blocks of eight words are present in a 16-slot block map.
    uc.mem_write(player, struct.pack("<I", vtable))
    uc.mem_write(player + 0x750, struct.pack("<I", key_manager))
    uc.mem_write(player + 0x7B0, struct.pack("<5I", 0, deque_table, 16, 0, 90))
    pointers = [ring_data + i * 0x1000 for i in range(12)] + [0] * 4
    uc.mem_write(deque_table, struct.pack("<16I", *pointers))
    # A 16-byte block stores eight 16-bit samples. Fill the startup history N.
    for block in range(12):
        uc.mem_write(ring_data + block * 0x1000, bytes(16))

    # The input object is controlled; updateInput/device polling is excluded.
    uc.mem_write(key_manager, struct.pack("<I", keymap))
    uc.mem_write(keymap, struct.pack("<I", keymap_vtable))
    uc.mem_write(keymap_vtable + 4, struct.pack("<I", stop + 0x100))
    uc.mem_write(stop + 0x100, b"\xc3")
    uc.mem_write(vtable + 0x54, struct.pack("<I", 0x00487020))
    setter_stub = stop + 0x200
    uc.mem_write(vtable + 8, struct.pack("<I", setter_stub))

    observed: dict[str, object] = {"matcher_calls": 0, "samples": [],
                                   "invalid_memory": None, "setter_actions": [],
                                   "cleanup_reached": False, "handler_branch_reached": False}
    handler_active = {"value": False}

    def hook(machine, address: int, _size: int, _user: object) -> None:
        if address == 0x0046C8E0:
            # Preserve the caller-supplied KeyInput fields and return from the
            # physical/device refresh only.
            esp = machine.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_ESP, esp + 4)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == 0x00487020:
            observed["matcher_calls"] += 1
        elif address == 0x00463530:
            esp = machine.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, 1)
            machine.reg_write(UC_X86_REG_ESP, esp + 4)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address in (0x00487890, 0x00439850, 0x00487990, 0x00468E80,
                         0x0048A700, 0x00456C80, 0x00489E90, 0x0048A220):
            # Controlled game-state/resource queries needed to isolate the
            # handler dispatch; the branch and all intervening PE logic run.
            esp = machine.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            values = {0x00487890: 0, 0x00439850: 1, 0x00487990: 0,
                      0x00468E80: 1, 0x0048A700: 0, 0x00456C80: action_node,
                      0x00489E90: 0, 0x0048A220: 0}
            machine.reg_write(UC_X86_REG_EAX, values[address])
            machine.reg_write(UC_X86_REG_ESP, esp + (12 if address in (0x00489E90, 0x0048A220) else 4))
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address in (0x0048A380, 0x0048A470, 0x0048A560):
            esp = machine.reg_read(UC_X86_REG_ESP)
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, 0)
            machine.reg_write(UC_X86_REG_ESP, esp + 4)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == setter_stub:
            esp = machine.reg_read(UC_X86_REG_ESP)
            action_id = struct.unpack("<H", machine.mem_read(esp + 4, 2))[0]
            observed["setter_actions"].append(action_id)
            machine.mem_write(player + 0x13C, struct.pack("<H", action_id))
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, 1)
            machine.reg_write(UC_X86_REG_ESP, esp + 8)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == 0x0046CAC0:
            observed["cleanup_reached"] = True
            if handler_active["value"]:
                machine.emu_stop()
        elif address == 0x0060BE83:
            observed["handler_branch_reached"] = True

    def invalid_memory(machine, access: int, address: int, size: int,
                       value: int, _user: object) -> bool:
        observed["invalid_memory"] = {
            "access": access, "address": hex(address), "size": size,
            "ip": hex(machine.reg_read(UC_X86_REG_EIP)),
        }
        return False

    uc.hook_add(UC_HOOK_CODE, hook)
    uc.hook_add(UC_HOOK_MEM_INVALID, invalid_memory)
    states = ((0, "neutral"), (1, "right"), (0, "neutral"), (1, "right"))
    trace = []
    for horizontal, label in states:
        uc.mem_write(player + 0x754, struct.pack("<8i", horizontal, 0, 0, 0, 0, 0, 0, 0))
        uc.mem_write(player + 0x774, bytes(0x20))
        sp = stack + 0xEFF0
        uc.mem_write(sp, struct.pack("<I", stop))
        uc.reg_write(UC_X86_REG_ECX, player)
        uc.reg_write(UC_X86_REG_ESP, sp)
        uc.reg_write(UC_X86_REG_EIP, 0x0046D5D0)
        try:
            uc.emu_start(0x0046D5D0, stop, count=100000)
        except Exception as exc:
            raise RuntimeError(f"input update failed at {observed['invalid_memory']}") from exc
        if uc.reg_read(UC_X86_REG_EIP) != stop:
            raise RuntimeError(f"update returned at {uc.reg_read(UC_X86_REG_EIP):#x}")
        head = struct.unpack("<I", uc.mem_read(player + 0x7BC, 4))[0]
        size = struct.unpack("<I", uc.mem_read(player + 0x7C0, 4))[0]
        block = (head + size - 1) // 8 % 16
        offset = (head + size - 1) % 8
        data_ptr = struct.unpack("<I", uc.mem_read(deque_table + block * 4, 4))[0]
        sample = struct.unpack("<H", uc.mem_read(data_ptr + offset * 2, 2))[0]
        motion_bits = struct.unpack("<I", uc.mem_read(player + 0x7C4, 4))[0]
        trace.append({"input": label, "sample": sample, "head": head, "size": size,
                      "motion_bits": motion_bits})

    # Continue through the full Suika handleInputs entry. The action 200 dash
    # state is seeded because this handler compares against 0xc8 (not 300);
    # the generated KeyInput itself comes from the preceding original updates.
    observed["setter_actions"] = []
    observed["cleanup_reached"] = False
    observed["handler_branch_reached"] = False
    uc.mem_write(player + 0x13C, struct.pack("<H", 200))
    uc.mem_write(player + 0x104, struct.pack("<b", 1))
    uc.mem_write(player + 0x158, struct.pack("<I", player_info))
    uc.mem_write(player + 0x15C, struct.pack("<I", action_node))
    uc.mem_write(player_info + 0x4C, struct.pack("<I", 0x20))
    uc.mem_write(action_node + 0x12, struct.pack("<H", 0))
    uc.mem_write(player + 0x784, struct.pack("<I", 1))
    uc.mem_write(player + 0x49E, struct.pack("<H", 1000))
    handler_sp = stack + 0xEFF0
    uc.mem_write(handler_sp, struct.pack("<8I", stop, 0, 0, 0, 0, 0, 0, 0))
    uc.reg_write(UC_X86_REG_ECX, player)
    uc.reg_write(UC_X86_REG_ESP, handler_sp)
    uc.reg_write(UC_X86_REG_EIP, 0x00609DC0)
    handler_active["value"] = True
    try:
        uc.emu_start(0x00609DC0, stop, count=200000)
    except Exception as exc:
        raise RuntimeError(f"full Suika handler failed at {observed['invalid_memory']}") from exc
    handler_trace = {
        "entry": "0x609dc0", "branch": "0x60be83",
        "seeded_precondition_action": 200,
        "branch_reached": observed["handler_branch_reached"],
        "current_key_input": list(struct.unpack("<2i", uc.mem_read(player + 0x754, 8))),
        "motion_matcher_bit": struct.unpack("<I", uc.mem_read(player + 0x7C4, 4))[0] & 1,
        "setter_actions": observed["setter_actions"],
        "action_after": struct.unpack("<H", uc.mem_read(player + 0x13C, 2))[0],
        "cleanup_entry_reached": observed["cleanup_reached"],
    }

    result = {
        "schema": 1,
        "reference_sha256": digest,
        "layout": {"table_offset": "Player+0x7b4", "block_count": 16,
                   "offset": "Player+0x7bc", "size": "Player+0x7c0",
                   "block_capacity": 8, "allocated_blocks": 12},
        "scope": "One Unicorn machine executes original input update 0x46d5d0, matcher 0x487020 and full Suika handleInputs entry 0x609dc0 through branch 0x60be83. Device refresh, state/resource queries, ground query and virtual setAction body are controlled; action 200 and facing right are seeded. Execution stops at cleanup entry 0x46cac0; its original body is independently exercised by x86_suika_418_handler_branch_probe.py.",
        "matcher_calls": observed["matcher_calls"],
        "trace": trace,
        "final_motion_bits": struct.unpack("<I", uc.mem_read(player + 0x7C4, 4))[0],
        "suika_handler": handler_trace,
        "passed": observed["matcher_calls"] == 4 and
                  trace[-1]["motion_bits"] & 1 != 0 and
                  all(row["size"] == 90 for row in trace) and
                  handler_trace["current_key_input"] == [1, 0] and
                  handler_trace["branch_reached"] and
                  handler_trace["seeded_precondition_action"] == 200 and
                  handler_trace["motion_matcher_bit"] == 1 and
                  handler_trace["setter_actions"] == [418] and
                  handler_trace["action_after"] == 418 and
                  handler_trace["cleanup_entry_reached"],
    }
    if not result["passed"]:
        raise AssertionError(json.dumps(result, indent=2))
    return result


def main() -> None:
    result = run()
    output = ROOT / "artifacts/x86-suika-input-matcher.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
