import unittest
from tools.x86_box_transform_probe import transform
from tools.x86_player_pair_hit_probe import run

class OriginalBoxTransformTests(unittest.TestCase):
    def test_full_world_units_and_facing(self):
        box=(-40,-120,80,0)
        self.assertEqual(transform(box,480,25,1),(440,-145,560,-25))
        self.assertEqual(transform(box,480,25,-1),(400,-145,520,-25))

    def test_ceil_position_before_local_box_translation(self):
        self.assertEqual(transform((-40,-120,80,0),480.75,25.25,1),(441,-146,561,-26))
        self.assertEqual(transform((-40,-120,80,0),480.25,25.75,1),(441,-146,561,-26))
        self.assertEqual(transform((-40,-120,80,0),-0.25,-0.75,1),(-40,-120,80,0))

    def test_udonge_first_attack_pose_contacts_in_original_pe(self):
        result=run(character='udonge',action_id=409,attack_sequence=1,
                   attack_frame=0,positions=((279,25),(321,0)))
        self.assertEqual(result['geometry']['return_value'],1)
        self.assertEqual(result['direct_damage_helper'],400)

    def test_udonge_dash_first_pose_contacts_in_original_pe(self):
        result=run(character='udonge',action_id=408,attack_sequence=1,
                   attack_frame=0,positions=((480,0),(530,0)))
        self.assertEqual(result['geometry']['return_value'],1)
        self.assertEqual(result['direct_damage_helper'],800)
