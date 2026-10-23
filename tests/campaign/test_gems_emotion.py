import json
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock

from module.campaign.gems_farming import GemsEmotion
from module.exception import CampaignEnd, ScriptEnd


class GemsEmotionTest(unittest.TestCase):
    def make_emotion(self, fleet=1, mode='calculate_ignore', change='ship'):
        values = dict(Emotion_Mode=mode, Campaign_Use2xBook=False,
                      GemsFarming_ChangeVanguard=change,
                      Fleet_FleetOrder='fleet1_standby_fleet2_all' if fleet == 2
                      else 'fleet1_all_fleet2_standby')
        for index in (1, 2):
            for key, value in dict(Value=5, Record=datetime.now(), Control='prevent_red_face',
                                   Recover='not_in_dormitory', Oath=False,
                                   Onsen=False, SinkShip=False).items():
                values['Emotion_Fleet{}{}'.format(index, key)] = value
        config = SimpleNamespace(**values)
        config.set_record = Mock(side_effect=lambda **kwargs: config.__dict__.update(kwargs))
        config.task_delay = Mock()
        return GemsEmotion(config)

    def test_active_fleet_reduction_and_record(self):
        for fleet in (1, 2):
            emotion = self.make_emotion(fleet)
            emotion.reduce(fleet)
            self.assertEqual(emotion.fleet.fleet, fleet)
            self.assertEqual(getattr(emotion.config, 'Emotion_Fleet{}Value'.format(fleet)), 3)
            self.assertEqual(getattr(emotion.config, 'Emotion_Fleet{}Value'.format(3-fleet)), 5)

    def test_low_emotion_changes_ships_or_delays(self):
        for change, exception in [('ship', CampaignEnd), ('disabled', ScriptEnd)]:
            emotion = self.make_emotion(change=change)
            with self.assertRaises(exception):
                emotion.check_reduce(4)
            if change == 'disabled':
                emotion.config.task_delay.assert_called_once()
            else:
                self.assertTrue(emotion.config.GEMS_EMOTION_TRIGGERED)

    def test_ignore_does_not_trigger_control(self):
        emotion = self.make_emotion(mode='ignore')
        emotion.check_reduce(100)
        emotion.wait(1)
        self.assertFalse(hasattr(emotion.config, 'GEMS_EMOTION_TRIGGERED'))

    def test_oath_and_recovery_settings_apply_to_attack_fleet(self):
        emotion = self.make_emotion(2)
        self.assertEqual(emotion.fleet.speed, 2)
        emotion.config.Emotion_Fleet2Oath = True
        emotion.config.Emotion_Fleet2Recover = 'dormitory_floor_2'
        self.assertEqual(emotion.fleet.speed, 6)

    def test_ui_settings_are_editable(self):
        with open('module/config/argument/args.json', encoding='utf-8') as stream:
            args = json.load(stream)['GemsFarming']['Emotion']
        for key in ('Mode', 'Fleet1Control', 'Fleet1Recover', 'Fleet1Oath',
                    'Fleet2Control', 'Fleet2Recover', 'Fleet2Oath'):
            self.assertNotEqual(args[key].get('display'), 'hide', key)


if __name__ == '__main__':
    unittest.main()
