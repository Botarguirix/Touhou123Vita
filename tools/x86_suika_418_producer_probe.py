#!/usr/bin/env python3
"""Extract the pinned PE's common movement branch that requests Suika action 418."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "local/python-deps"))
import struct
REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
PRODUCER = 0x004B0AC2
ACTION_PUSH = 0x004B0B04


def probe(exe: Path = ROOT / "original/th123.exe") -> dict[str, object]:
    try:
        from capstone import Cs, CS_ARCH_X86, CS_MODE_32
        import pefile
    except ImportError as exc:
        raise RuntimeError("install the project's local Capstone and pefile dependencies") from exc
    raw = exe.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != REFERENCE_SHA256:
        raise ValueError(f"reference PE SHA-256 mismatch: {digest}")
    pe = pefile.PE(data=raw)
    base = pe.OPTIONAL_HEADER.ImageBase
    start, end = PRODUCER, 0x004B0B39
    code = pe.get_data(start - base, end - start)
    decoder = Cs(CS_ARCH_X86, CS_MODE_32)
    instructions = [
        {"address": ins.address, "mnemonic": ins.mnemonic, "operands": ins.op_str,
         "bytes": ins.bytes.hex()}
        for ins in decoder.disasm(code, start)
    ]
    by_address = {row["address"]: row for row in instructions}
    if not any(row["address"] == ACTION_PUSH and row["mnemonic"] == "push"
               and row["operands"] == "0x1a2" for row in instructions):
        raise AssertionError("action-418 push moved or changed")
    vtable_load = by_address.get(0x004B0B15)
    virtual_call = by_address.get(0x004B0B29)
    if not vtable_load or not virtual_call or virtual_call["mnemonic"] != "call":
        raise AssertionError("action-418 virtual setter callsite changed")
    return {
        "schema": 1,
        "reference_sha256": digest,
        "producer_va": hex(PRODUCER),
        "action": 418,
        "action_push_va": hex(ACTION_PUSH),
        "virtual_setter_call_va": hex(0x004B0B29),
        "requested_action": "0x1a2 (418)",
        "observed_guards": [
            "current action at Player+0x13c is zero",
            "current horizontal KeyInput at Player+0x754 or buffered horizontal KeyInput at Player+0x774, multiplied by facing at Player+0x104, indicates forward motion",
            "Player+0x758 (KeyInput) equals zero",
            "Player+0x778 (buffered vertical KeyInput) is not tested by this branch",
            "0x489610(0x1a2) resource/action query passes the BX comparison",
        ],
        "before_setter": "writes 0.0 to Player+0x12c, then invokes Player vtable slot +8 with 418",
        "after_setter": "tail-jumps to 0x46cac0",
        "deque_layout": {
            "player_member": "0x7b0",
            "debug_proxy": "deque+0x0",
            "block_table": "deque+0x4",
            "block_count": "deque+0x8",
            "offset": "deque+0xc",
            "size": "deque+0x10",
            "player_block_table": "0x7b4",
            "player_block_count": "0x7b8",
            "player_offset": "0x7bc",
            "player_size": "0x7c0",
            "block_capacity": 8,
            "source": "local/SokuLib/src/Deque.hpp and PE accesses at 0x46cc90/0x42cf90",
        },
        "instructions": instructions,
        "scope": "Static report plus optional dynamic execution of the original action-418 decision block 0x4b0ac2 and cleanup 0x46cac0. The fixture uses controlled grounded, move-lock, and virtual-setAction services; input update and matcher are not part of this dynamic run.",
    }


def run_guard_case(*, current_horizontal: int = 1, buffered_horizontal: int = 0,
                   current_vertical: int = 0, buffered_vertical: int = 1,
                   facing: int = 1, grounded: bool = True,
                   available_lock: int = 100, comparison: int = 0) -> dict[str, object]:
    """Execute the original 418 producer block and 46cac0 cleanup under Unicorn.

    The stack/register context is the interior method context at 0x4b0ac2.
    Only the grounded query, PAT move-lock lookup, and virtual setAction body
    are controlled; branch conditions and input cleanup execute from the PE.
    """
    try:
        import pefile
        from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32
        from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX,
                                       UC_X86_REG_ECX, UC_X86_REG_EIP,
                                       UC_X86_REG_ESI, UC_X86_REG_ESP)
    except ImportError as exc:
        raise RuntimeError("install local pefile and Unicorn dependencies") from exc
    raw = (ROOT / "original/th123.exe").read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != REFERENCE_SHA256:
        raise ValueError(f"reference PE SHA-256 mismatch: {digest}")
    pe = pefile.PE(data=raw)
    base = pe.OPTIONAL_HEADER.ImageBase
    image = pe.get_memory_mapped_image()
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(base, (len(image) + 0xFFF) & ~0xFFF)
    uc.mem_write(base, image)
    player, vtable, stack, stop = 0x01000000, 0x01100000, 0x02000000, 0x03000000
    set_action_stub = stop + 0x100
    for address, size in ((player, 0x1000), (vtable, 0x1000),
                          (stack, 0x10000), (stop, 0x1000)):
        uc.mem_map(address, size)
    uc.mem_write(stop, b"\xf4")
    uc.mem_write(player, struct.pack("<I", vtable))
    uc.mem_write(vtable + 8, struct.pack("<I", set_action_stub))
    uc.mem_write(player + 0x13C, struct.pack("<H", 0))
    uc.mem_write(player + 0x104, struct.pack("<b", facing))
    uc.mem_write(player + 0x754, struct.pack("<ii", current_horizontal, current_vertical))
    uc.mem_write(player + 0x774, struct.pack("<ii", buffered_horizontal, buffered_vertical))
    # The shared epilogue at the successful action branch consumes these saved
    # registers, two locals, and the method's caller return address.
    sp = stack + 0xEFF0
    uc.mem_write(sp, struct.pack("<7I", 0xAAAA0001, 0, player, 0,
                                 0x11111111, 0x22222222, stop))
    observed: dict[str, object] = {"setter_actions": [], "stop_reason": None}

    def hook(machine, address: int, _size: int, _user: object) -> None:
        esp = machine.reg_read(UC_X86_REG_ESP)
        if address == 0x00463530:
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, int(grounded))
            machine.reg_write(UC_X86_REG_ESP, esp + 4)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == 0x00489610:
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            action_id = struct.unpack("<H", machine.mem_read(esp + 4, 2))[0]
            observed["move_lock_action"] = action_id
            machine.reg_write(UC_X86_REG_EAX, available_lock & 0xFFFF)
            machine.reg_write(UC_X86_REG_ESP, esp + 8)  # ret 4
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == set_action_stub:
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            action_id = struct.unpack("<H", machine.mem_read(esp + 4, 2))[0]
            observed["setter_actions"].append(action_id)
            machine.mem_write(player + 0x13C, struct.pack("<H", action_id))
            machine.reg_write(UC_X86_REG_EAX, 1)
            machine.reg_write(UC_X86_REG_ESP, esp + 8)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address in (0x004B0B39, 0x004B0C95):
            observed["stop_reason"] = hex(address)
            machine.emu_stop()

    uc.hook_add(UC_HOOK_CODE, hook)
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_ECX, player)
    uc.reg_write(UC_X86_REG_ESI, player)
    uc.reg_write(UC_X86_REG_EBX, comparison & 0xFFFFFFFF)
    uc.reg_write(UC_X86_REG_EIP, PRODUCER)
    uc.emu_start(PRODUCER, stop, count=10000)
    observed.update({
        "current": [current_horizontal, current_vertical],
        "buffered": [buffered_horizontal, buffered_vertical],
        "facing": facing,
        "grounded": grounded,
        "available_lock": available_lock,
        "comparison": comparison,
        "action_after": struct.unpack("<H", uc.mem_read(player + 0x13C, 2))[0],
        "buffered_after": list(struct.unpack("<8I", uc.mem_read(player + 0x774, 0x20))),
        "eip_after": hex(uc.reg_read(UC_X86_REG_EIP)),
    })
    return observed


def dynamic_cases() -> list[dict[str, object]]:
    cases = [
        ("forward_vertical_buffer", {}, True),
        ("backward_rejected", {"current_horizontal": -1}, False),
        ("no_horizontal_rejected", {"current_horizontal": 0}, False),
        ("vertical_current_nonzero_rejected", {"current_vertical": 1}, False),
        ("current_forward_without_vertical_buffer", {"buffered_vertical": 0}, True),
        ("airborne_rejected", {"grounded": False}, False),
        ("move_lock_rejected", {"available_lock": 0, "comparison": 1}, False),
        ("buffered_forward", {"current_horizontal": 0, "buffered_horizontal": 1}, True),
    ]
    results = []
    for name, kwargs, should_set in cases:
        row = run_guard_case(**kwargs)
        row["case"] = name
        row["expected_set"] = should_set
        row["passed"] = (row["setter_actions"] == ([418] if should_set else []))
        if should_set:
            row["passed"] = row["passed"] and row["action_after"] == 418
            row["passed"] = row["passed"] and row["buffered_after"] == [0] * 8
        results.append(row)
    if not all(row["passed"] for row in results):
        raise AssertionError(f"dynamic action-418 producer cases failed: {results}")
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", nargs="?", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dynamic", action="store_true",
                        help="execute eight controlled action-418 guard cases in the pinned PE")
    args = parser.parse_args()
    result = probe(args.exe)
    if args.dynamic:
        cases = dynamic_cases()
        result["dynamic_cases"] = cases
        result["dynamic_cases_passed"] = sum(bool(r["passed"]) for r in cases)
    rendered = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    if args.dynamic:
        print(json.dumps({"dynamic_cases": len(cases), "passed": sum(r["passed"] for r in cases),
                          "rows": cases}, indent=2))
    print(json.dumps({"action": result["action"], "producer": result["producer_va"],
                      "setter_call": result["virtual_setter_call_va"],
                      "instruction_count": len(result["instructions"]),
                      "scope": result["scope"]}, indent=2))


if __name__ == "__main__":
    main()
