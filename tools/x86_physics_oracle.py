"""Execute the original Player horizontal-physics helper on synthetic states."""
import hashlib
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "local/python-deps"))
import pefile
from unicorn import Uc, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_ECX, UC_X86_REG_ESP

REFERENCE_SHA256 = "f0db93660ceb8635a1921e0ba4686fcfbd5c492311dee6ef7061b7bada16731e"
PHYSICS = 0x463550
PLAYER = 0x01000000
OPPONENT = 0x01100000
STACK = 0x02000000
STOP = 0x03000000


class PhysicsOracle:
    def __init__(self, exe: Path):
        raw = exe.read_bytes()
        self.sha256 = hashlib.sha256(raw).hexdigest()
        if self.sha256 != REFERENCE_SHA256:
            raise ValueError(f"reference SHA256 mismatch: {self.sha256}")
        pe = pefile.PE(data=raw)
        image = pe.get_memory_mapped_image()
        base = pe.OPTIONAL_HEADER.ImageBase
        self.uc = Uc(UC_ARCH_X86, UC_MODE_32)
        self.uc.mem_map(base, (len(image) + 0xFFF) & ~0xFFF)
        self.uc.mem_write(base, image)
        for address, size in ((PLAYER, 0x1000), (OPPONENT, 0x1000),
                              (STACK, 0x10000), (STOP, 0x1000)):
            self.uc.mem_map(address, size)
        self.uc.hook_add(UC_HOOK_CODE, self._hook)

    @staticmethod
    def _hook(uc, address, _size, _user):
        if address == STOP:
            uc.emu_stop()

    def step(self, x: float, speed_x: float, direction: int,
             speed_power: float = 1.0, opponent_additional_speed_x: float = 0.0,
             player_motion_lock: int = 0, opponent_motion_lock: int = 0):
        if direction not in (-1, 1):
            raise ValueError("direction must be -1 or 1")
        u = self.uc
        player = bytearray(0x1000)
        struct.pack_into("<I", player, 0x170, OPPONENT)
        struct.pack_into("<h", player, 0x196, player_motion_lock)
        struct.pack_into("<f", player, 0x0EC, x)
        struct.pack_into("<f", player, 0x0F4, speed_x)
        struct.pack_into("<f", player, 0x564, speed_power)
        player[0x104] = direction & 0xFF
        opponent = bytearray(0x1000)
        struct.pack_into("<h", opponent, 0x4A8, opponent_motion_lock)
        struct.pack_into("<f", opponent, 0x74C, opponent_additional_speed_x)
        u.mem_write(PLAYER, bytes(player))
        u.mem_write(OPPONENT, bytes(opponent))
        esp = STACK + 0xEFFC
        u.mem_write(esp, struct.pack("<I", STOP))
        u.reg_write(UC_X86_REG_ECX, PLAYER)
        u.reg_write(UC_X86_REG_ESP, esp)
        u.emu_start(PHYSICS, STOP, count=10000)
        result = struct.unpack("<f", u.mem_read(PLAYER + 0x0EC, 4))[0]
        return result


def vectors():
    return (
        (100.0, 4.5, 1, 1.0, 0.0, 104.5),
        (100.0, 4.5, -1, 1.0, 0.0, 95.5),
        (100.0, 4.5, 1, 2.0, 0.0, 109.0),
        (100.0, 4.5, -1, 1.0, 0.5, 95.0),
        # With stage-lock byte +0x571 clear, the original helper takes the
        # direct integration branch and does not apply the arena clamps.
        (42.0, -4.5, 1, 1.0, 0.0, 37.5),
        (1238.0, 4.5, 1, 1.0, 0.0, 1242.5),
    )
