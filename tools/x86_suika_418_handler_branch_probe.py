#!/usr/bin/env python3
"""Execute Suika's original action-418 branch and cleanup from handleInputs."""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))
REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
ENTRY = 0x0060BE34
BRANCH = 0x0060BE83
CLEANUP = 0x0046CAC0
GROUND_QUERY = 0x00463530
MOVE_LOCK = 0x00489610


def run(*, action: int = 200, horizontal: int = 1, facing: int = 1,
        vertical: int = 0, grounded: bool = True, move_lock: int = 1000,
        comparison: int = 100) -> dict[str, object]:
    import pefile
    from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_MODE_32
    from unicorn.x86_const import (UC_X86_REG_EAX, UC_X86_REG_EBX,
                                   UC_X86_REG_EDI, UC_X86_REG_EIP,
                                   UC_X86_REG_ESI, UC_X86_REG_ESP)
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
    setter = stop + 0x100
    for address, size in ((player, 0x1000), (vtable, 0x1000),
                          (stack, 0x10000), (stop, 0x1000)):
        uc.mem_map(address, size)
    uc.mem_write(stop, b"\xf4")
    uc.mem_write(player, struct.pack("<I", vtable))
    uc.mem_write(vtable + 8, struct.pack("<I", setter))
    uc.mem_write(player + 0x13C, struct.pack("<H", action))
    uc.mem_write(player + 0x104, struct.pack("<b", facing))
    uc.mem_write(player + 0x754, struct.pack("<ii", horizontal, vertical))
    uc.mem_write(player + 0x774, bytes(0x20))
    uc.mem_write(player + 0x49E, struct.pack("<H", 1000))
    sp = stack + 0xEFF0
    uc.mem_write(sp, struct.pack("<7I", 0xAAAA0001, 0, player, 0,
                                 0, 0, stop))
    observed: dict[str, object] = {"branch_reached": False, "setter_actions": [],
                                   "move_lock_queries": [], "cleanup_reached": False}

    def hook(machine, address: int, _size: int, _user: object) -> None:
        esp = machine.reg_read(UC_X86_REG_ESP)
        if address == BRANCH:
            observed["branch_reached"] = True
        elif address == GROUND_QUERY:
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, int(grounded))
            machine.reg_write(UC_X86_REG_ESP, esp + 4)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == MOVE_LOCK:
            action_id = struct.unpack("<H", machine.mem_read(esp + 4, 2))[0]
            observed["move_lock_queries"].append(action_id)  # type: ignore[union-attr]
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, move_lock & 0xFFFF)
            machine.reg_write(UC_X86_REG_ESP, esp + 8)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == setter:
            action_id = struct.unpack("<H", machine.mem_read(esp + 4, 2))[0]
            observed["setter_actions"].append(action_id)  # type: ignore[union-attr]
            machine.mem_write(player + 0x13C, struct.pack("<H", action_id))
            ret = struct.unpack("<I", machine.mem_read(esp, 4))[0]
            machine.reg_write(UC_X86_REG_EAX, 1)
            machine.reg_write(UC_X86_REG_ESP, esp + 8)
            machine.reg_write(UC_X86_REG_EIP, ret)
        elif address == CLEANUP:
            observed["cleanup_reached"] = True

    uc.hook_add(UC_HOOK_CODE, hook)
    uc.reg_write(UC_X86_REG_ESP, sp)
    uc.reg_write(UC_X86_REG_ESI, player)
    uc.reg_write(UC_X86_REG_EBX, 200)  # this handler block's action-200 comparison
    uc.reg_write(UC_X86_REG_EDI, comparison)  # current action frame/comparison
    uc.reg_write(UC_X86_REG_EIP, ENTRY)
    uc.emu_start(ENTRY, stop, count=10000)
    observed.update({"entry": hex(ENTRY), "branch": hex(BRANCH),
                     "requested_action": 418,
                     "action_after": struct.unpack("<H", uc.mem_read(player + 0x13C, 2))[0],
                     "buffered_after": list(struct.unpack("<8I", uc.mem_read(player + 0x774, 0x20))),
                     "input": {"action_before": action, "horizontal": horizontal,
                               "vertical": vertical, "facing": facing,
                               "grounded": grounded, "move_lock": move_lock,
                               "comparison": comparison},
                     "reference_sha256": digest})
    should_set = (action == 200 and grounded and horizontal * facing > 0
                  and vertical == 0)
    observed["passed"] = (
        bool(observed["branch_reached"]) == should_set
        and ((418 in observed["setter_actions"]) == should_set)
        and (observed["action_after"] == 418 if should_set else True)
        and (bool(observed["cleanup_reached"]) if should_set else True)
        and (observed["buffered_after"] == [0] * 8 if should_set else True)
    )
    if not observed["passed"]:
        raise AssertionError(json.dumps(observed, indent=2))
    return observed


def cases() -> list[dict[str, object]]:
    variants = [
        ("forward_from_dash_200", {}, True),
        ("neutral_input_rejected", {"horizontal": 0}, False),
        ("backward_input_rejected", {"horizontal": -1}, False),
        ("vertical_input_rejected", {"vertical": 1}, False),
        ("airborne_rejected", {"grounded": False}, False),
        ("move_lock_does_not_gate_this_branch", {"move_lock": 0, "comparison": 1}, True),
    ]
    result = []
    for name, kwargs, expected in variants:
        row = run(**kwargs)
        row.update({"case": name, "expected_set": expected})
        result.append(row)
    return result


def main() -> None:
    rows = cases()
    report = {"schema": 1, "entry": hex(ENTRY), "cases": rows,
              "passed": sum(bool(row["passed"]) for row in rows),
              "scope": "Executes the original Suika 0x609dc0 block at 0x60be34 through branch 0x60be83, virtual setter and original 0x46cac0 cleanup. Ground query, move-lock and concrete virtual setter are controlled; earlier handler dispatch and device input polling are not included."}
    out = ROOT / "artifacts/x86-suika-418-handler-branch.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": len(rows), "passed": report["passed"], "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
