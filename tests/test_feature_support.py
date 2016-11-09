import fixtures
from io import open
import mock
import os
import sys
import testtools

import requests_mock
import rxv

FAKE_IP = '10.0.0.0'
DESC_XML = 'http://%s/YamahaRemoteControl/desc.xml' % FAKE_IP


def sample_content(name):
    with open('tests/samples/%s' % name, encoding='utf-8') as f:
        return f.read()


class TestFeaturesV675(testtools.TestCase):

    @requests_mock.mock()
    def setUp(self, m):
        super(TestFeaturesV675, self).setUp()
        m.get(DESC_XML, text=sample_content('rx-v675-desc.xml'))
        self.rec = rxv.RXV(FAKE_IP)

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
