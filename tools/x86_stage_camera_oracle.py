#!/usr/bin/env python3
"""Run the pinned PE's camera target method for controlled fighter positions."""
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local" / "python-deps"))
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import (UC_X86_REG_ECX, UC_X86_REG_EIP, UC_X86_REG_ESP,
                               UC_X86_REG_FPCW, UC_X86_REG_FPSW)

EXPECTED_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
IMAGE_BASE = 0x00400000
CAMERA_TARGET = 0x00428E20
CAMERA_UPDATE = 0x00429040
CAMERA_UPDATE_STOP = 0x004293DE
CAMERA_CONSTRUCTOR = 0x00429560
SQRT_CALL = 0x00428EC0


def original_camera_state(x0, x1, y0, y1, *, flags=(0, 0, 0),
                          initial=(0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0),
                          trace=None):
    """Run only the target method with explicit synthetic camera fields.

    Its Y output is state-dependent; use original_camera_constructor for
    gameplay-like initialization and vertical-camera evidence.
    """
    exe = ROOT / "original" / "th123.exe"
    image = exe.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected PE SHA-256: {digest}")
    pe = pefile.PE(data=image, fast_load=True)
    image_size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xFFF) & ~0xFFF
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(IMAGE_BASE, image_size)
    for section in pe.sections:
        uc.mem_write(IMAGE_BASE + section.VirtualAddress, section.get_data())

    # FUN_00428e20 calls the MSVC sqrt wrapper at this site. FSQRT preserves
    # the original x87 evaluation while keeping the oracle independent of CRT.
    sqrt_offset = pe.get_offset_from_rva(SQRT_CALL - IMAGE_BASE)
    if image[sqrt_offset:sqrt_offset + 5] != bytes.fromhex("e8 2b 72 3f 00"):
        raise ValueError("Pinned camera sqrt callsite changed")
    uc.mem_write(SQRT_CALL, bytes.fromhex("d9 fa 90 90 90"))

    uc.mem_map(0x00900000, 0x5000)
    uc.mem_map(0x00910000, 0x2000)
    camera = 0x00900000
    points = (0x00901000, 0x00901004, 0x00901008, 0x0090100C)
    for address, value in zip(points, (x0, x1, y0, y1)):
        uc.mem_write(address, struct.pack("<f", value))
    for field, address in zip((0x44, 0x48, 0x4C, 0x50), points):
        uc.mem_write(camera + field, struct.pack("<I", address))
    # Camera state: center X/Y, target/current zoom, previous zoom, and limits.
    for offset, value in zip((0x0, 0x4, 0x8, 0x14, 0x28, 0x20, 0x24), initial):
        uc.mem_write(camera + offset, struct.pack("<f", value))
    for offset, value in zip((0x2C, 0x2D, 0x2E), flags):
        uc.mem_write(camera + offset, bytes((value,)))
    stack_pointer = 0x00910F00
    return_address = 0x00904000
    uc.mem_write(stack_pointer, struct.pack("<I", return_address))
    uc.reg_write(UC_X86_REG_ESP, stack_pointer)
    uc.reg_write(UC_X86_REG_ECX, camera)
    uc.reg_write(UC_X86_REG_FPCW, 0x037F)
    uc.reg_write(UC_X86_REG_FPSW, 0)
    trace_points = {0x00428F67, 0x00428F76, 0x00428FAA, 0x00428FBD,
                    0x00428FC1, 0x00429020, 0x00429037}
    def trace_hook(machine, address, size, data):
        if trace is None or address not in trace_points:
            return
        esp = machine.reg_read(UC_X86_REG_ESP)
        locals_ = tuple(struct.unpack("<f", machine.mem_read(esp + off, 4))[0]
                        for off in (0x10, 0x14, 0x18))
        fields_ = tuple(struct.unpack("<f", machine.mem_read(camera + off, 4))[0]
                        for off in (0x0, 0x4, 0x8, 0x14, 0x20, 0x24))
        trace.append((address, locals_, fields_))
    uc.hook_add(UC_HOOK_CODE, trace_hook)
    uc.emu_start(CAMERA_TARGET, return_address, timeout=1_000_000, count=100_000)
    fields = (0x0, 0x4, 0x8, 0x54, 0x58)
    return tuple(struct.unpack("<f", uc.mem_read(camera + field, 4))[0]
                 for field in fields)


def original_target_zoom(x0, x1, y0, y1):
    return original_camera_state(x0, x1, y0, y1)[2]


def original_camera_update(x0, x1, y0, y1, *, state=(320.0, 420.0, 1.0,
                                                       1.0, 320.0, 420.0),
                           flags=(0, 0, 0), fixed=(0.0, 0.0), trace=None):
    """Run the PE's per-frame zoom/center easing up to matrix construction."""
    image = (ROOT / "original" / "th123.exe").read_bytes()
    if hashlib.sha256(image).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Unexpected PE SHA-256")
    pe = pefile.PE(data=image, fast_load=True)
    image_size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xFFF) & ~0xFFF
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(IMAGE_BASE, image_size)
    for section in pe.sections:
        uc.mem_write(IMAGE_BASE + section.VirtualAddress, section.get_data())
    uc.mem_map(0x00900000, 0x5000)
    uc.mem_map(0x00910000, 0x2000)
    camera = 0x00900000
    points = (0x00901000, 0x00901004, 0x00901008, 0x0090100C)
    for address, value in zip(points, (x0, x1, y0, y1)):
        uc.mem_write(address, struct.pack("<f", value))
    for field, address in zip((0x44, 0x48, 0x4C, 0x50), points):
        uc.mem_write(camera + field, struct.pack("<I", address))
    for offset, value in zip((0x0, 0x4, 0x8, 0x14, 0x18, 0x1C), state):
        uc.mem_write(camera + offset, struct.pack("<f", value))
    for offset, value in zip((0x2C, 0x2D, 0x2E), flags):
        uc.mem_write(camera + offset, bytes((value,)))
    for offset, value in zip((0x20, 0x24), fixed):
        uc.mem_write(camera + offset, struct.pack("<f", value))
    stack_pointer = 0x00910F00
    uc.mem_write(stack_pointer, struct.pack("<I", 0x00904000))
    uc.reg_write(UC_X86_REG_ESP, stack_pointer)
    uc.reg_write(UC_X86_REG_ECX, camera)
    uc.reg_write(UC_X86_REG_FPCW, 0x037F)
    uc.reg_write(UC_X86_REG_FPSW, 0)
    pcs = []
    trace_points = {0x00429182, 0x004291DC, 0x0042920D,
                    0x00429279, 0x0042928E, CAMERA_UPDATE_STOP}
    uc.hook_add(UC_HOOK_CODE,
                lambda machine, address, size, data:
                (pcs.append(address),
                 trace.append((address, tuple(
                     struct.unpack("<f", machine.mem_read(camera + off, 4))[0]
                     for off in (0, 4, 8, 0x14, 0x18, 0x1C)),
                     tuple(struct.unpack("<f", machine.mem_read(machine.reg_read(
                         UC_X86_REG_ESP) + off, 4))[0] for off in (4, 8))))
                 if trace is not None and address in trace_points else None,
                 machine.emu_stop() if address == CAMERA_UPDATE_STOP else None))
    try:
        uc.emu_start(CAMERA_UPDATE, 0x00429400, timeout=1_000_000,
                     count=100_000)
    except Exception as error:
        raise RuntimeError(f"camera update fault at {uc.reg_read(UC_X86_REG_EIP):08x}; "
                           f"last PCs {[hex(pc) for pc in pcs[-80:]]}: {error}") from error
    return tuple(struct.unpack("<f", uc.mem_read(camera + offset, 4))[0]
                 for offset in (0x14, 0x18, 0x1C, 0x0C, 0x10))


def original_camera_constructor(x0, y0, x1, y1):
    """Execute the pinned PE's full camera init, target refresh, and first update."""
    image = (ROOT / "original" / "th123.exe").read_bytes()
    if hashlib.sha256(image).hexdigest() != EXPECTED_SHA256:
        raise ValueError("Unexpected PE SHA-256")
    pe = pefile.PE(data=image, fast_load=True)
    image_size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xFFF) & ~0xFFF
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(IMAGE_BASE, image_size)
    for section in pe.sections:
        uc.mem_write(IMAGE_BASE + section.VirtualAddress, section.get_data())
    sqrt_offset = pe.get_offset_from_rva(SQRT_CALL - IMAGE_BASE)
    if image[sqrt_offset:sqrt_offset + 5] != bytes.fromhex("e8 2b 72 3f 00"):
        raise ValueError("Pinned camera sqrt callsite changed")
    uc.mem_write(SQRT_CALL, bytes.fromhex("d9 fa 90 90 90"))
    uc.mem_map(0x00900000, 0x5000)
    uc.mem_map(0x00910000, 0x2000)
    camera = 0x00900000
    points = (0x00901000, 0x00901004, 0x00901008, 0x0090100C)
    for address, value in zip(points, (x0, y0, x1, y1)):
        uc.mem_write(address, struct.pack("<f", value))
    stack_pointer = 0x00910F00
    return_address = 0x00904000
    uc.mem_write(stack_pointer, struct.pack("<IIIII", return_address, *points))
    uc.reg_write(UC_X86_REG_ESP, stack_pointer)
    uc.reg_write(UC_X86_REG_ECX, camera)
    uc.reg_write(UC_X86_REG_FPCW, 0x037F)
    uc.reg_write(UC_X86_REG_FPSW, 0)
    uc.hook_add(UC_HOOK_CODE,
                lambda machine, address, size, data:
                machine.emu_stop() if address == return_address else None)
    uc.emu_start(CAMERA_CONSTRUCTOR, 0x00904100, timeout=1_000_000,
                 count=1_000_000)
    offsets = (0x0, 0x4, 0x8, 0x0C, 0x10, 0x14, 0x18, 0x1C,
               0x30, 0x34, 0x38, 0x3C, 0x40)
    return tuple(struct.unpack("<f", uc.mem_read(camera + offset, 4))[0]
                 for offset in offsets)


def main():
    vectors = ((200, 0, 200, 0), (200, 0, 300, 100),
               (200, 0, 900, 0), (200, 0, 2200, 0),
               (200, 100, 440, 200))
    print("x0\ty0\tx1\ty1\ttarget_x\ttarget_y\tzoom\tcurrent_x\tcurrent_y\tviewport_y")
    for vector in vectors:
        state = original_camera_constructor(*vector)
        print("\t".join(map(str, (*vector, state[0], state[1], state[2],
                                 state[6], state[7], state[4]))))


if __name__ == "__main__":
    main()
