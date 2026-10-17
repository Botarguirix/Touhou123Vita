#!/usr/bin/env python3
"""Run the original Suwako object-list constructor and action-808 factory path.

The manager/list and object constructors and createObject x86 body execute from
the pinned PE. Heap allocation, locks, trig/RNG and renderer are controlled.
Action 808 loop flags and frame durations are decoded from the local DAT.
"""
from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "local/python-deps"))
sys.path.insert(0, str(ROOT))

import pefile
from tools.extract_pat_pose_metadata import action_sequence_metadata, read_pat
from unicorn import Uc, UC_ARCH_X86, UC_HOOK_CODE, UC_HOOK_MEM_INVALID, UC_MODE_32
from unicorn.x86_const import (
    UC_X86_REG_EAX, UC_X86_REG_EBP, UC_X86_REG_EBX, UC_X86_REG_ECX,
    UC_X86_REG_EDI, UC_X86_REG_EDX, UC_X86_REG_EIP, UC_X86_REG_ESI,
    UC_X86_REG_ESP,
)

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
LIST, OWNER, OWNER_DATA, PAT_MAP = 0x01000000, 0x01010000, 0x01020000, 0x01030000
NIL, ACTION_NODE = 0x01031000, 0x01032000
CUSTOM = 0x01037000
STACK, STOP, HEAP = 0x02000000, 0x03000000, 0x01100000


def read_u32(uc: Uc, address: int) -> int:
    return struct.unpack("<I", uc.mem_read(address, 4))[0]


def read_f32(uc: Uc, address: int) -> float:
    return struct.unpack("<f", uc.mem_read(address, 4))[0]


class Suwako808FactoryProbe:
    def __init__(self, exe: Path, dat_dir: Path | None = None,
                 intercept_box_transforms: bool = False,
                 character: str = "suwako", action_id: int = 808):
        raw = exe.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if self.sha256 != REFERENCE_SHA256:
            raise ValueError(f"reference SHA-256 mismatch: {self.sha256}")
        pe = pefile.PE(data=raw)
        self.base = pe.OPTIONAL_HEADER.ImageBase
        image = pe.get_memory_mapped_image()
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(self.base, (len(image) + 0xFFF) & ~0xFFF)
        self.uc.mem_write(self.base, image)
        for address, size in ((LIST, 0x10000), (OWNER, 0x10000),
                              (OWNER_DATA, 0x10000), (PAT_MAP, 0x80000),
                              (STACK, 0x10000), (STOP, 0x1000), (HEAP, 0x100000)):
            self.uc.mem_map(address, size)
        self.uc.mem_map(0, 0x1000)  # FS:[0] used by the original SEH prologues
        self.uc.mem_map(0x03100000, 0x1000)  # controlled KERNEL32 module image
        self.uc.mem_write(STOP, b"\xf4")
        self.uc.mem_write(STOP + 0x10, b"\xc2\x04\x00")  # lock init/lock/unlock service
        self.uc.mem_write(0x00857114, struct.pack("<I", STOP + 0x10))
        self.uc.mem_write(0x00857118, struct.pack("<I", STOP + 0x10))
        self.uc.mem_write(0x0085711C, struct.pack("<I", STOP + 0x10))
        self._windows_api_stub_names: dict[int, str] = {}
        self._tls_slots: dict[int, int] = {}
        self._last_error = 0
        self.host_termination: dict[str, object] | None = None
        if action_id == 801:
            # Minimal, signature-correct KERNEL32 contracts for the CRT
            # delay-load/pointer-decoder path exercised by action 801.
            api_stubs = {
                "TlsGetValue": (0x20, b"\x31\xc0\xc2\x04\x00", 0x857190),
                "GetModuleHandleA": (0x30, b"\xb8\x00\x00\x10\x03\xc2\x04\x00", 0x857188),
                "GetProcAddress": (0x40, b"\xb8\x50\x00\x00\x03\xc2\x08\x00", 0x857184),
                "DecodePointer": (0x50, b"\x8b\x44\x24\x04\xc2\x04\x00", None),
                "GetLastError": (0x60, b"\x31\xc0\xc3", 0x857038),
                "SetLastError": (0x70, b"\x31\xc0\xc2\x04\x00", 0x8571A4),
                "GetCurrentThreadId": (0x80, b"\xb8\x01\x00\x00\x00\xc3", 0x8571A8),
                "IsDebuggerPresent": (0x90, b"\x31\xc0\xc3", 0x857160),
                "SetUnhandledExceptionFilter": (0xA0, b"\x31\xc0\xc2\x04\x00", 0x85715C),
                "UnhandledExceptionFilter": (0xB0, b"\x31\xc0\xc2\x04\x00", 0x857158),
                "InterlockedIncrement": (0xC0, b"\x8b\x44\x24\x04\xff\x00\x8b\x00\xc2\x04\x00", 0x8571A0),
                "GetCurrentProcess": (0xF0, b"\xb8\xff\xff\xff\xff\xc3", 0x857154),
            }
            for name, (offset, code, iat) in api_stubs.items():
                address = STOP + offset
                self.uc.mem_write(address, code)
                self._windows_api_stub_names[address] = name
                if iat is not None:
                    self.uc.mem_write(iat, struct.pack("<I", address))
            self._windows_api_stub_names[STOP + 0xD0] = "TlsAlloc"
            self._windows_api_stub_names[STOP + 0xD4] = "TlsSetValue"
            self._windows_api_stub_names[STOP + 0x120] = "TerminateProcess"
            self.uc.mem_write(0x00857194, struct.pack("<I", STOP + 0xD0))
            self.uc.mem_write(0x00857198, struct.pack("<I", STOP + 0xD4))
            self.uc.mem_write(0x00857150, struct.pack("<I", STOP + 0x120))
            fake = bytearray(0x400)
            fake[:2] = b"MZ"
            struct.pack_into("<I", fake, 0x3C, 0x80)
            fake[0x80:0x84] = b"PE\0\0"
            struct.pack_into("<H", fake, 0x86, 1)  # one section
            struct.pack_into("<H", fake, 0x94, 0xE0)  # optional header size
            fake[0x178:0x180] = b".text\0\0\0"
            self.uc.mem_write(0x03100000, bytes(fake))
            # The static CRT normally initializes its invalid-parameter
            # callback before game objects update; use a no-op callback slot.
            self.uc.mem_write(0x0089AB48, struct.pack("<I", 1))
            self.uc.mem_write(0x0089AB54, struct.pack("<I", STOP + 0xE0))
            self.uc.mem_write(STOP + 0xE0, b"\xc3")
        self.heap_cursor = HEAP
        self.allocations: list[dict[str, object]] = []
        self.events: list[dict[str, object]] = []
        self.box_transform_calls: list[dict[str, object]] = []
        self.box_transform_entries: list[dict[str, object]] = []
        self.object_ptr = 0
        self.intercept_box_transforms = intercept_box_transforms
        self._trace_active = False
        self._code_trace: list[int] = []
        self._invalid_memory: list[dict[str, int]] = []
        self.dat_dir = dat_dir or ROOT / "original"
        self.character = character
        self.action_id = action_id
        self.pat_fixture: dict[str, object] = {}
        self.uc.hook_add(UC_HOOK_CODE, self._hook)
        self.uc.hook_add(UC_HOOK_MEM_INVALID, self._invalid_mem_hook)

    def _invalid_mem_hook(self, _uc: Uc, access: int, address: int, size: int,
                          value: int, _user: object) -> bool:
        self._invalid_memory.append({"access": access, "address": address,
                                     "size": size, "value": value})
        return False

    def _return(self, esp: int, cleanup: int = 0) -> None:
        uc = self.uc
        target = read_u32(uc, esp)
        uc.reg_write(UC_X86_REG_ESP, esp + 4 + cleanup)
        uc.reg_write(UC_X86_REG_EIP, target)

    def _hook(self, uc: Uc, address: int, _size: int, _user: object) -> None:
        if address in self._windows_api_stub_names:
            self.events.append({"address": "windows-api", "name": self._windows_api_stub_names[address]})
            esp = uc.reg_read(UC_X86_REG_ESP)
            if address == STOP + 0x20:  # TlsGetValue(DWORD index)
                index = read_u32(uc, esp + 4)
                self._last_error = 87 if index == 0xFFFFFFFF else 0
                uc.reg_write(UC_X86_REG_EAX, self._tls_slots.get(index, 0))
                self._return(esp, cleanup=4)
                return
            if address == STOP + 0x60:  # GetLastError()
                uc.reg_write(UC_X86_REG_EAX, self._last_error)
                self._return(esp)
                return
            if address == STOP + 0x70:  # SetLastError(DWORD)
                self._last_error = read_u32(uc, esp + 4)
                uc.reg_write(UC_X86_REG_EAX, 0)
                self._return(esp, cleanup=4)
                return
            if address == STOP + 0x50:  # DecodePointer(PVOID)
                encoded = read_u32(uc, esp + 4)
                self.events.append({"address": "windows-api-arg", "name": "DecodePointer",
                                    "value": hex(encoded)})
                uc.reg_write(UC_X86_REG_EAX, encoded)
                self._return(esp, cleanup=4)
                return
            if address == STOP + 0xD0:  # TlsAlloc() -> stable synthetic slot
                uc.reg_write(UC_X86_REG_EAX, 0x40)
                self._return(esp)
                return
            if address == STOP + 0xD4:  # TlsSetValue(index, value)
                index, value = read_u32(uc, esp + 4), read_u32(uc, esp + 8)
                self._tls_slots[index] = value
                uc.reg_write(UC_X86_REG_EAX, 1)
                self._return(esp, cleanup=8)
                return
            if address == STOP + 0x120:  # TerminateProcess(handle, exit_code)
                self.host_termination = {"api": "TerminateProcess",
                                         "process": hex(read_u32(uc, esp + 4)),
                                         "exit_code": hex(read_u32(uc, esp + 8))}
                uc.emu_stop()
                return
        if self._trace_active:
            self._code_trace.append(address)
            del self._code_trace[:-300]
            if address < 0x1000:
                self.events.append({"address": "invalid-low-code-fetch", "eip": hex(address)})
                uc.emu_stop()
                return
        if address == STOP:
            uc.emu_stop()
            return
        if address in (0x004640B0, 0x00464200):
            esp = uc.reg_read(UC_X86_REG_ESP)
            source, destination = read_u32(uc, esp + 4), read_u32(uc, esp + 8)
            self.box_transform_entries.append({"helper": hex(address),
                                               "source": hex(source),
                                               "destination": hex(destination)})
            if not self.intercept_box_transforms:
                return
        esp = uc.reg_read(UC_X86_REG_ESP)
        if address == 0x0081FBDC:
            size = read_u32(uc, esp + 4)
            ptr = (self.heap_cursor + 0xF) & ~0xF
            self.heap_cursor = ptr + size + 0x10
            uc.mem_write(ptr, bytes(size))
            self.allocations.append({"size": size, "address": hex(ptr), "zeroed": True})
            if size == 0x3AC:
                self.object_ptr = ptr
            uc.reg_write(UC_X86_REG_EAX, ptr)
            self._return(esp)  # cdecl; caller removes size
        elif address in (0x00783D70, 0x00783BA0, 0x00783DE0,
                         0x00784020, 0x00783A70, 0x00464930,
                         0x00799000, 0x004652A0, 0x00465A2A):
            self.events.append({"address": hex(address), "ecx": hex(uc.reg_read(UC_X86_REG_ECX))})
        elif address == 0x0043A250:
            obj = uc.reg_read(UC_X86_REG_ECX)
            self.events.append({"address": "0x43a250", "object": hex(obj),
                                "color": bytes(uc.mem_read(obj + 0x110, 4)).hex(),
                                "action": struct.unpack("<H", uc.mem_read(obj + 0x13C, 2))[0],
                                "sequence": struct.unpack("<H", uc.mem_read(obj + 0x13E, 2))[0]})
            self._return(esp)
        elif address in (0x004095F0, 0x00409580):
            angle = struct.unpack("<f", uc.mem_read(esp + 4, 4))[0]
            value = math.sin(math.radians(angle if address == 0x004095F0 else angle - 90.0))
            stub, output = STOP + 0x100, STOP + 0x200
            uc.mem_write(stub, b"\xd9\x05" + struct.pack("<I", output) + b"\xc3")
            uc.mem_write(output, struct.pack("<f", value))
            uc.reg_write(UC_X86_REG_EIP, stub)
        elif address == 0x004099F0:
            uc.reg_write(UC_X86_REG_EAX, 0)
            self._return(esp)  # cdecl; action initializer removes arguments
        elif address == 0x004397F0:
            # Controlled stage-floor service, returned through x87 ST(0).
            stub, output = STOP + 0x300, STOP + 0x400
            uc.mem_write(stub, b"\xd9\x05" + struct.pack("<I", output) + b"\xc3")
            uc.mem_write(output, struct.pack("<f", 500.0))
            uc.reg_write(UC_X86_REG_EIP, stub)
        elif address == 0x0048CE90:
            # No collision in this controlled open-air fixture.
            uc.reg_write(UC_X86_REG_EAX, 0)
            self._return(esp, cleanup=12)
        elif address in (0x004640B0, 0x00464200) and self.intercept_box_transforms:
            # Preserve the box values while isolating the game's coordinate
            # conversion, which depends on initialized stage/camera globals.
            source, destination = read_u32(uc, esp + 4), read_u32(uc, esp + 8)
            raw_box = bytes(uc.mem_read(source, 16))
            self.box_transform_calls.append({"helper": hex(address), "source": hex(source),
                                             "destination": hex(destination),
                                             "input_box": list(struct.unpack("<4i", raw_box))})
            uc.mem_write(destination, raw_box)
            self._return(esp, cleanup=8)

    def _prepare_pat(self) -> None:
        uc = self.uc
        pat_resource = None
        for archive in ("th123c.dat", "th123b.dat", "th123a.dat"):
            path = self.dat_dir / archive
            if not path.is_file():
                continue
            pat_resource = read_pat(path, f"data/character/{self.character}/{self.character}.pat")
            if pat_resource is not None:
                self.pat_fixture["archive"] = archive
                break
        if pat_resource is None:
            raise FileNotFoundError(f"{self.character} PAT not found in {self.dat_dir}")
        pat, pat_sha256 = pat_resource
        sequences = action_sequence_metadata(pat, self.action_id)
        sequences.sort(key=lambda row: int(row["sequence"]))
        if not sequences or [row["sequence"] for row in sequences] != list(range(len(sequences))):
            raise ValueError(f"PAT action {self.action_id} sequences are missing or non-contiguous")
        if any(len(row["frames"]) > 0x1000 // 0xA8 for row in sequences):
            raise ValueError(f"action {self.action_id} frame data exceeds the probe's safe PAT fixture region")
        self.pat_fixture.update({"resource": f"data/character/{self.character}/{self.character}.pat",
                                 "action": self.action_id, "pat_sha256": pat_sha256,
                                 "sequences": sequences})
        uc.mem_write(PAT_MAP + 4, struct.pack("<I", NIL))
        uc.mem_write(PAT_MAP + 8, struct.pack("<I", 1))
        uc.mem_write(NIL, struct.pack("<III", ACTION_NODE, ACTION_NODE, ACTION_NODE))
        uc.mem_write(NIL + 0x15, b"\x01")
        uc.mem_write(ACTION_NODE, struct.pack("<III", NIL, NIL, NIL))
        uc.mem_write(ACTION_NODE + 0x0C, struct.pack("<I", self.action_id))
        sequence_nodes = [PAT_MAP + 0x8000 + i * 0x1000 for i in range(len(sequences))]
        uc.mem_write(ACTION_NODE + 0x10, struct.pack("<I", sequence_nodes[0]))
        for index, (seq, metadata) in enumerate(zip(sequence_nodes, sequences)):
            frames = metadata["frames"]
            frame = PAT_MAP + 0x10000 + index * 0x1000
            uc.mem_write(seq + 4, struct.pack("<II", frame, frame + len(frames) * 0xA8))
            uc.mem_write(seq + 0x14, bytes((int(metadata["loop_mode"]),)))
            next_node = sequence_nodes[(index + 1) % len(sequence_nodes)]
            previous_node = sequence_nodes[(index - 1) % len(sequence_nodes)]
            uc.mem_write(seq + 0x18, struct.pack("<I", next_node))
            uc.mem_write(seq + 0x1C, struct.pack("<I", previous_node))
            for frame_index, frame_data in enumerate(frames):
                pose = frame + frame_index * 0xA8
                uc.mem_write(pose + 8, struct.pack("<H", int(frame_data["duration"])))
                # CharacterFrameData embeds three Soku vectors: hurt boxes
                # at +0x58, attack boxes at +0x68, and extra-box pointers at
                # +0x78. Their begin/end/capacity pointers start +4/+8/+0xc.
                for vector_offset, key, stride, type_offset in (
                        (0x58, "hurt_boxes", 16, 0), (0x68, "attack_boxes", 16, 0x100)):
                    boxes = frame_data[key]
                    box_start = PAT_MAP + 0x20000 + (index * 0x8000) + (frame_index * 0x800) + type_offset
                    box_end = box_start + len(boxes) * stride
                    uc.mem_write(pose + vector_offset, struct.pack("<4I", 0, box_start, box_end, box_end))
                    if boxes:
                        uc.mem_write(box_start, b"".join(struct.pack("<4i", *box) for box in boxes))
                extra_count = len(frame_data["attack_boxes"])
                extra = PAT_MAP + 0x30000 + (index * 0x8000) + (frame_index * 0x800)
                extra_end = extra + extra_count * 4
                uc.mem_write(pose + 0x78, struct.pack("<4I", 0, extra, extra_end, extra_end))
                if extra_count:
                    # Null means no frame-specific rotated replacement box.
                    uc.mem_write(extra, bytes(extra_count * 4))

    def _sync_box_data(self, obj: int) -> dict[str, object]:
        """Run the original GameObject frame-to-box synchronization routine."""
        uc = self.uc
        sp = STACK + 0xA000 - 4
        uc.mem_write(sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESP, sp)
        uc.reg_write(UC_X86_REG_ECX, obj)
        uc.reg_write(UC_X86_REG_EIP, 0x00465E10)
        try:
            self._code_trace.clear()
            self._trace_active = True
            uc.emu_start(0x00465E10, STOP, count=250000)
        except Exception as exc:
            trail = ",".join(hex(item) for item in self._code_trace[-24:])
            raise RuntimeError(f"box synchronization faulted at EIP={uc.reg_read(UC_X86_REG_EIP):#x}: {exc}; trace={trail}") from exc
        finally:
            self._trace_active = False
        if uc.reg_read(UC_X86_REG_EIP) != STOP:
            raise RuntimeError(f"box synchronization did not return: EIP={uc.reg_read(UC_X86_REG_EIP):#x}")

        def boxes(offset: int, count_offset: int) -> list[list[int]]:
            count = uc.mem_read(obj + count_offset, 1)[0]
            return [list(struct.unpack("<4i", uc.mem_read(obj + offset + i * 16, 16)))
                    for i in range(count)]

        return {
            "frame_data_pointer": hex(read_u32(uc, obj + 0x1C0)),
            "hit_box_count": uc.mem_read(obj + 0x1CB, 1)[0],
            "hurt_box_count": uc.mem_read(obj + 0x1CC, 1)[0],
            "hurt_boxes": boxes(0x1D0, 0x1CC),
            "hit_boxes": boxes(0x220, 0x1CB),
            "collision_box_pointer": hex(read_u32(uc, obj + 0x348)),
        }

    def run(self, ticks: int = 40) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(LIST, bytes(0x10000))
        uc.mem_write(OWNER, bytes(0x10000))
        uc.mem_write(OWNER_DATA, bytes(0x10000))
        uc.mem_write(PAT_MAP, bytes(0x10000))
        self.heap_cursor = HEAP
        self.allocations.clear()
        self.events.clear()
        self.box_transform_calls.clear()
        self.box_transform_entries.clear()
        self._invalid_memory.clear()
        self.host_termination = None

        # Execute the actual object-list/handle-manager constructor.
        sp = STACK + 0x7000 - 4
        uc.mem_write(sp, struct.pack("<I", STOP))
        uc.reg_write(UC_X86_REG_ESP, sp)
        uc.reg_write(UC_X86_REG_ECX, LIST)
        uc.reg_write(UC_X86_REG_EIP, 0x00783D70)
        uc.emu_start(0x00783D70, STOP, count=100000)

        self._prepare_pat()
        # Owner fields consumed/copied by 0x784020.
        uc.mem_write(OWNER + 0x130, struct.pack("<I", OWNER_DATA))
        uc.mem_write(OWNER + 0x160, struct.pack("<I", PAT_MAP))
        uc.mem_write(OWNER + 0x170, struct.pack("<I", OWNER))
        uc.mem_write(OWNER + 0x6F8, struct.pack("<I", LIST))
        uc.mem_write(LIST + 0x64, struct.pack("<I", OWNER))
        uc.mem_write(CUSTOM, struct.pack("<3f", -20.0, 12.0, 1.0))

        # createObject(this=list, parent=null, owner, action, x, y, dir, layer,
        # customData, customDataSize); stdcall cleanup is performed by callee.
        sp = STACK + 0x8000 - 4
        args = (STOP, 0, OWNER, self.action_id,
                struct.unpack("<I", struct.pack("<f", 300.0))[0],
                struct.unpack("<I", struct.pack("<f", 400.0))[0],
                1, 1, CUSTOM, 3)
        uc.mem_write(sp, struct.pack("<10I", *args))
        uc.reg_write(UC_X86_REG_ESP, sp)
        uc.reg_write(UC_X86_REG_ECX, LIST)
        uc.reg_write(UC_X86_REG_EIP, 0x00784020)
        error = None
        try:
            uc.emu_start(0x00784020, STOP, count=250000)
        except Exception as exc:  # preserve boundary details in the report
            error = f"{type(exc).__name__}: {exc}"

        factory_completed = error is None and uc.reg_read(UC_X86_REG_EIP) == STOP
        factory_return_state = None
        updates: list[dict[str, object]] = []
        update_error = None
        if factory_completed:
            obj = uc.reg_read(UC_X86_REG_EAX)
            self.object_ptr = obj
            box_sync = {"sequence_1": self._sync_box_data(obj)}
            # Examine seq.0 using the original selector and box synchronizer;
            # the actual action-808 update later changes sequence as usual.
            sequence_zero = PAT_MAP + 0x8000
            uc.mem_write(obj + 0x13E, struct.pack("<H", 0))
            uc.mem_write(obj + 0x15C, struct.pack("<I", sequence_zero))
            pose_sp = STACK + 0xA800 - 4
            uc.mem_write(pose_sp, struct.pack("<II", STOP, 0))
            uc.reg_write(UC_X86_REG_ESP, pose_sp)
            uc.reg_write(UC_X86_REG_ECX, obj)
            uc.reg_write(UC_X86_REG_EIP, 0x00464B50)
            uc.emu_start(0x00464B50, STOP, count=100000)
            if uc.reg_read(UC_X86_REG_EIP) != STOP:
                raise RuntimeError("original setPose did not return for seq.0 probe")
            box_sync["sequence_0"] = self._sync_box_data(obj)
            # Restore the factory's natural seq.1 pose before ticking the
            # action dispatcher below.
            sequence_one = PAT_MAP + 0x9000
            uc.mem_write(obj + 0x13E, struct.pack("<H", 1))
            uc.mem_write(obj + 0x15C, struct.pack("<I", sequence_one))
            pose_sp = STACK + 0xA800 - 4
            uc.mem_write(pose_sp, struct.pack("<II", STOP, 0))
            uc.reg_write(UC_X86_REG_ESP, pose_sp)
            uc.reg_write(UC_X86_REG_ECX, obj)
            uc.reg_write(UC_X86_REG_EIP, 0x00464B50)
            uc.emu_start(0x00464B50, STOP, count=100000)
            if uc.reg_read(UC_X86_REG_EIP) != STOP:
                raise RuntimeError("original setPose did not return while restoring seq.1")
            box_sync["sequence_1_restored"] = self._sync_box_data(obj)
            self.box_sync = box_sync
            factory_return_state = {
                "address": hex(obj),
                "vtable": hex(read_u32(uc, obj)),
                "action": struct.unpack("<H", uc.mem_read(obj + 0x13C, 2))[0],
                "sequence": struct.unpack("<H", uc.mem_read(obj + 0x13E, 2))[0],
                "render_color_hex": bytes(uc.mem_read(obj + 0x110, 4)).hex(),
                "alpha": uc.mem_read(obj + 0x113, 1)[0],
                "position": [read_f32(uc, obj + 0xEC), read_f32(uc, obj + 0xF0)],
                "custom_data_pointer": hex(read_u32(uc, obj + 0x35C)),
                "field_34c_u32": read_u32(uc, obj + 0x34C),
            }
            for tick in range(ticks):
                # The original manager stops dispatching an object after its
                # callback sets +0x34c to zero. Do not drive a dead object
                # manually and turn its terminal decrement into underflow.
                if read_u32(uc, obj + 0x34C) == 0:
                    break
                tick_sp = STACK + 0x9000 - 4
                uc.mem_write(tick_sp, struct.pack("<I", STOP))
                uc.reg_write(UC_X86_REG_ESP, tick_sp)
                uc.reg_write(UC_X86_REG_ECX, obj)
                uc.reg_write(UC_X86_REG_EIP, 0x007876D0)
                self._code_trace.clear()
                self._trace_active = True
                try:
                    uc.emu_start(0x007876D0, STOP, count=100000)
                except Exception as exc:
                    trail = ",".join(hex(item) for item in self._code_trace[-120:])
                    regs = {name: f"{uc.reg_read(register):#x}" for name, register in (
                        ("eax", UC_X86_REG_EAX), ("ebx", UC_X86_REG_EBX),
                        ("ecx", UC_X86_REG_ECX), ("edx", UC_X86_REG_EDX),
                        ("esi", UC_X86_REG_ESI), ("edi", UC_X86_REG_EDI),
                        ("ebp", UC_X86_REG_EBP), ("esp", UC_X86_REG_ESP))}
                    update_error = (f"tick {tick + 1}: {type(exc).__name__}: {exc}; "
                                    f"EIP={uc.reg_read(UC_X86_REG_EIP):#x}; regs={regs}; trace={trail}")
                    break
                finally:
                    self._trace_active = False
                if self.host_termination is not None:
                    update_error = (f"tick {tick + 1}: CRT requested process termination "
                                    f"{self.host_termination}")
                    break
                if uc.reg_read(UC_X86_REG_EIP) != STOP:
                    trail = ",".join(hex(item) for item in self._code_trace[-120:])
                    update_error = (f"tick {tick + 1}: stopped outside PE at "
                                    f"EIP={uc.reg_read(UC_X86_REG_EIP):#x}; trace={trail}")
                    break
                updates.append({
                    "tick": tick + 1,
                    "dispatcher_eax": hex(uc.reg_read(UC_X86_REG_EAX)),
                    "field_34c_u32": read_u32(uc, obj + 0x34C),
                    "x": read_f32(uc, obj + 0xEC),
                    "y": read_f32(uc, obj + 0xF0),
                    "vx": read_f32(uc, obj + 0xF4),
                    "vy": read_f32(uc, obj + 0xF8),
                    "render_alpha": uc.mem_read(obj + 0x113, 1)[0],
                    "sequence": struct.unpack("<H", uc.mem_read(obj + 0x13E, 2))[0],
                    "pose": struct.unpack("<H", uc.mem_read(obj + 0x140, 2))[0],
                    "pose_subframe": struct.unpack("<H", uc.mem_read(obj + 0x142, 2))[0],
                })
                if update_error:
                    break

        obj = self.object_ptr
        object_state = None
        if obj:
            object_state = {
                "address": hex(obj),
                "vtable": hex(read_u32(uc, obj)),
                "action": struct.unpack("<H", uc.mem_read(obj + 0x13C, 2))[0],
                "sequence": struct.unpack("<H", uc.mem_read(obj + 0x13E, 2))[0],
                "render_color_hex": bytes(uc.mem_read(obj + 0x110, 4)).hex(),
                "alpha": uc.mem_read(obj + 0x113, 1)[0],
                "position": [read_f32(uc, obj + 0xEC), read_f32(uc, obj + 0xF0)],
                "custom_data_pointer": hex(read_u32(uc, obj + 0x35C)),
                "field_34c_u32": read_u32(uc, obj + 0x34C),
            }
        return {
            "reference_sha256": self.sha256,
            "factory_completed": factory_completed,
            "stopped_eip": hex(uc.reg_read(UC_X86_REG_EIP)),
            "error": error,
            "factory_return_object": factory_return_state,
            "object_after_updates": object_state,
            "updates": updates,
            "update_error": update_error,
            "dispatcher_reached_terminal_field_zero": bool(
                updates and updates[-1]["field_34c_u32"] == 0),
            "manager_removed_object": None,
            "allocations": self.allocations,
            "events": self.events,
            "box_transform_calls": self.box_transform_calls,
            "box_transform_entries": self.box_transform_entries,
            "invalid_memory_accesses": self._invalid_memory,
            "box_sync": getattr(self, "box_sync", None),
            "pat_fixture": self.pat_fixture,
            "scope": "Original list constructor, object constructor, 0x784020 factory and 0x7876d0 update dispatcher execute from the PE when they return at STOP. The dispatcher probe stops on +0x34c==0; it does not invoke manager cleanup. PAT durations/hurt/attack boxes are decoded from the hashed local DAT and installed into CharacterFrameData vector layout; the original setPose and 0x465e10 box synchronizer execute for seq.0/1. The real action-808 descriptors do not reach 0x4640b0/0x464200 during this sync. Renderer, heap, locks, trig, RNG, stage floor and collision remain controlled. This is not a native game-loop or full scenario trace.",
        }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, default=ROOT / "original/th123.exe")
    parser.add_argument("--dat-dir", type=Path, default=ROOT / "original")
    parser.add_argument("--ticks", type=int, default=40)
    parser.add_argument("--character", default="suwako")
    parser.add_argument("--action", type=int, default=808)
    parser.add_argument("--copy-box-transform", action="store_true",
                        help="diagnostic only: intercept 0x4640b0/0x464200 and copy the source rectangle")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = Suwako808FactoryProbe(args.exe, args.dat_dir,
                intercept_box_transforms=args.copy_box_transform,
                character=args.character, action_id=args.action).run(ticks=args.ticks)
    output = args.output
    if output is None:
        output = (ROOT / "artifacts/x86-suwako-808-factory-probe.json"
                  if args.character == "suwako" and args.action == 808
                  else ROOT / f"artifacts/x86-{args.character}-{args.action}-factory-probe.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{args.character} action {args.action} factory probe: completed={report['factory_completed']} eip={report['stopped_eip']}")


if __name__ == "__main__":
    main()
