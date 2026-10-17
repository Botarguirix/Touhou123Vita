import unittest
from pathlib import Path

from tools.x86_physics_oracle import PhysicsOracle, vectors


class PhysicsOracleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        exe = Path("original/th123.exe")
        if not exe.is_file():
            raise unittest.SkipTest("local reference original/th123.exe is unavailable")
        cls.oracle = PhysicsOracle(exe)

    def test_horizontal_motion_follows_facing_and_speed_power(self):
        for x, vx, direction, power, opponent_vx, expected in vectors():
            with self.subTest(direction=direction, power=power,
                              opponent_vx=opponent_vx):
                actual = self.oracle.step(x, vx, direction, power, opponent_vx)
                self.assertAlmostEqual(actual, expected, places=5)

    def test_unlocked_stage_branch_does_not_apply_arena_clamps(self):
        # Player+0x571=0 selects the direct-integration branch. The other
        # branch's limits 40/1240 are guarded by stage-collision helpers.
        self.assertEqual(self.oracle.step(42.0, -4.5, 1), 37.5)
        self.assertEqual(self.oracle.step(1238.0, 4.5, 1), 1242.5)

    def test_player_or_opponent_motion_lock_skips_integration(self):
        # 00463550 returns before reading velocity if either +0x196 field is
        # nonzero. The zero-lock case is covered by the movement vectors.
        self.assertEqual(self.oracle.step(100.0, 4.5, 1,
                                         player_motion_lock=1), 100.0)
        self.assertEqual(self.oracle.step(100.0, 4.5, 1,
                                         opponent_motion_lock=1), 100.0)


if __name__ == "__main__":
    unittest.main()
