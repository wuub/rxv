import fixtures
from io import open
import mock
import os
import sys
import testtools

import requests_mock
import rxv

FAKE_IP = '10.0.0.0'


def sample_content(name):
    with open('tests/samples/%s' % name, encoding='utf-8') as f:
        return f.read()


class TestRXV(testtools.TestCase):

    def test_basic_object(self):
        rec = rxv.RXV(FAKE_IP)
        self.assertEqual(
            rec.ctrl_url,
            'http://%s/YamahaRemoteControl/ctrl' % FAKE_IP)
        self.assertEqual(
            rec.unit_desc_url,
            'http://%s/YamahaRemoteControl/desc.xml' % FAKE_IP)


class TestDesc(testtools.TestCase):

    @requests_mock.mock()
    def test_discover_zones(self, m):
        rec = rxv.RXV(FAKE_IP)
        m.get(rec.unit_desc_url, text=sample_content('rx-v675-desc.xml'))
        zones = rec.zone_controllers()
        self.assertEqual(len(zones), 2, zones)
        self.assertEqual(zones[0].zone, "Main_Zone")
        self.assertEqual(zones[1].zone, "Zone_2")
