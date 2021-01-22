from io import open

import requests_mock
import unittest


import rxv

FAKE_IP = '10.0.0.0'
DESC_XML = 'http://%s/YamahaRemoteControl/desc.xml' % FAKE_IP
CTRL_URL = 'http://%s/YamahaRemoteControl/ctrl' % FAKE_IP


def sample_content(name):
    with open('tests/samples/%s' % name, encoding='utf-8') as f:
        return f.read()


class TestFeaturesV675(unittest.TestCase):

    @requests_mock.mock()
    def setUp(self, m):
        super(TestFeaturesV675, self).setUp()
        m.get(DESC_XML, text=sample_content('rx-v675-desc.xml'))
        self.rec = rxv.RXV(CTRL_URL)

    def test_supports_method(self):
        rec = self.rec
        self.assertTrue(rec.supports_method("NET_RADIO", "Play_Info"))
        self.assertTrue(rec.supports_method("NET_RADIO", "Config"))
        self.assertTrue(
            rec.supports_method("NET_RADIO", "Play_Control", "Playback"))

        self.assertTrue(rec.supports_method("SERVER", "Play_Info"))
        self.assertTrue(rec.supports_method("SERVER", "Config"))
        self.assertTrue(
            rec.supports_method("SERVER", "Play_Control", "Playback"))

        self.assertFalse(rec.supports_method("HDMI1", "Play_Info"))
        self.assertFalse(rec.supports_method("HDMI1", "Config"))

        self.assertTrue(rec.supports_method("Tuner", "Play_Info"))
        self.assertTrue(rec.supports_method("Tuner", "Config"))
        self.assertFalse(
            rec.supports_method("Tuner", "Play_Control", "Playback"))

        self.assertTrue(
            rec.supports_method("Main_Zone", "Sound_Video", "Dialogue_Adjust", "Dialogue_Lvl"))

    def test_supports_play_method(self):
        rec = self.rec
        self.assertFalse(rec.supports_play_method("NET_RADIO", "Pause"))
        self.assertTrue(rec.supports_play_method("NET_RADIO", "Play"))
        self.assertTrue(rec.supports_play_method("NET_RADIO", "Stop"))
        self.assertFalse(rec.supports_play_method("NET_RADIO", "Skip Fwd"))
        self.assertFalse(rec.supports_play_method("NET_RADIO", "Skip Rev"))

        self.assertTrue(rec.supports_play_method("SERVER", "Pause"))
        self.assertTrue(rec.supports_play_method("SERVER", "Play"))
        self.assertTrue(rec.supports_play_method("SERVER", "Stop"))
        self.assertTrue(rec.supports_play_method("SERVER", "Skip Fwd"))
        self.assertTrue(rec.supports_play_method("SERVER", "Skip Rev"))

    def test_play_status_spotify(self):
        from defusedxml import cElementTree as ET
        res = ET.XML(sample_content('rx-v1030-spotify-response.xml'))
        self.assertTrue(
            rxv.RXV.safe_get(res, ["Playback_Info"]) == "Play"
        )
        self.assertEqual(
            'Lenny Kravitz',
            rxv.RXV.safe_get(res, rxv.rxv.ARTIST_OPTIONS)
        )
        self.assertEqual(
            'It\'s Enough',
            rxv.RXV.safe_get(res, rxv.rxv.ALBUM_OPTIONS)
        )
        self.assertEqual(
            'It\'s Enough',
            rxv.RXV.safe_get(res, rxv.rxv.SONG_OPTIONS)
        )
        self.assertEqual(
            '',
            rxv.RXV.safe_get(res, rxv.rxv.STATION_OPTIONS)
        )

    def test_play_status_netradio(self):
        from defusedxml import cElementTree as ET
        res = ET.XML(sample_content('rx-v1030-netradio-response.xml'))
        self.assertTrue(
            rxv.RXV.safe_get(res, ["Playback_Info"]) == "Play"
        )
        self.assertEqual(
            '',
            rxv.RXV.safe_get(res, rxv.rxv.ARTIST_OPTIONS)
        )
        self.assertEqual(
            'Undertow',
            rxv.RXV.safe_get(res, rxv.rxv.ALBUM_OPTIONS)
        )
        self.assertEqual(
            'Sober',
            rxv.RXV.safe_get(res, rxv.rxv.SONG_OPTIONS)
        )
        self.assertEqual(
            'NDR 2 (HH)',
            rxv.RXV.safe_get(res, rxv.rxv.STATION_OPTIONS)
        )

    def test_play_status_tuner(self):
        from defusedxml import cElementTree as ET
        res = ET.XML(sample_content('rx-v1030-tuner-response.xml'))
        src_name = "Tuner"
        self.assertTrue(
            rxv.RXV.safe_get(res, ["Playback_Info"]) == "Play"
            or src_name == "Tuner"
        )
        self.assertEqual(
            'ROCK M',
            rxv.RXV.safe_get(res, rxv.rxv.ARTIST_OPTIONS)
        )
        self.assertEqual(
            'RADIO & BOB!',
            rxv.RXV.safe_get(res, rxv.rxv.ALBUM_OPTIONS)
        )
        self.assertEqual(
            'Black Stone Cherry - Burnin\'_',
            rxv.RXV.safe_get(res, rxv.rxv.SONG_OPTIONS)
        )
        self.assertEqual(
            'RADIOBOB',
            rxv.RXV.safe_get(res, rxv.rxv.STATION_OPTIONS)
        )

    @requests_mock.mock()
    def test_playback_support(self, m):
        rec = self.rec
        # we need to mock this out so that .inputs() work
        m.post(rec.ctrl_url, text=sample_content('rx-v675-inputs-resp.xml'))

        support = rec.get_playback_support("NET RADIO")
        self.assertTrue(support.play)
        self.assertTrue(support.stop)
        self.assertFalse(support.pause)
        self.assertFalse(support.skip_f)
        self.assertFalse(support.skip_r)

        support = rec.get_playback_support("HDMI1")
        self.assertTrue(support.play)
        self.assertTrue(support.stop)
        self.assertTrue(support.pause)
        self.assertTrue(support.skip_f)
        self.assertTrue(support.skip_r)

        support = rec.get_playback_support("SERVER")
        self.assertTrue(support.play)
        self.assertTrue(support.stop)
        self.assertTrue(support.pause)
        self.assertTrue(support.skip_f)
        self.assertTrue(support.skip_r)

    @requests_mock.mock()
    def test_menu_cursor_support(self, m):
        rec = self.rec
        # we need to mock this out so that .inputs() work
        m.post(rec.ctrl_url, text=sample_content("rx-v675-inputs-resp.xml"))

        self.assertCountEqual(
            [
                rxv.rxv.CURSOR_DOWN,
                rxv.rxv.CURSOR_RETURN,
                rxv.rxv.CURSOR_RETURN_TO_HOME,
                rxv.rxv.CURSOR_SEL,
                rxv.rxv.CURSOR_UP,
            ],
            rec.supported_cursor_actions("NET RADIO"),
        )

        self.assertCountEqual(
            [
                rxv.rxv.CURSOR_DISPLAY,
                rxv.rxv.CURSOR_DOWN,
                rxv.rxv.CURSOR_LEFT,
                rxv.rxv.CURSOR_MENU,
                rxv.rxv.CURSOR_ON_SCREEN,
                rxv.rxv.CURSOR_OPTION,
                rxv.rxv.CURSOR_SEL,
                rxv.rxv.CURSOR_RETURN,
                rxv.rxv.CURSOR_RETURN_TO_HOME,
                rxv.rxv.CURSOR_RIGHT,
                rxv.rxv.CURSOR_TOP_MENU,
                rxv.rxv.CURSOR_UP,
            ],
            rec.supported_cursor_actions("HDMI1"),
        )

        self.assertCountEqual([], rec.supported_cursor_actions("TUNER"))
