import unittest
from tools.x86_player_reset_probe import reset_position
from tools.x86_stage_camera_oracle import original_camera_constructor

class PlayerResetTests(unittest.TestCase):
    def test_original_common_reset_positions_and_facing(self):
        self.assertEqual(reset_position(0),dict(x=480,y=0,vx=0,vy=0,facing=1))
        self.assertEqual(reset_position(1),dict(x=800,y=0,vx=0,vy=0,facing=-1))

    def test_original_camera_starts_centered_on_reset_players(self):
        left,right=reset_position(0),reset_position(1)
        state=original_camera_constructor(left['x'],left['y'],right['x'],right['y'])
        self.assertEqual((state[6],state[7],state[5]),(640,0,1))
