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


class TestRXV(unittest.TestCase):

    @requests_mock.mock()
    def test_basic_object(self, m):
        m.get(DESC_XML, text=sample_content('rx-v675-desc.xml'))
        rec = rxv.RXV(CTRL_URL)
        self.assertEqual(
            rec.unit_desc_url,
            'http://%s/YamahaRemoteControl/desc.xml' % FAKE_IP)


class TestDesc(unittest.TestCase):

    @requests_mock.mock()
    def test_discover_zones(self, m):
        m.get(DESC_XML, text=sample_content('rx-v675-desc.xml'))
        rec = rxv.RXV(CTRL_URL)
        zones = rec.zone_controllers()
        self.assertEqual(len(zones), 2, zones)
        self.assertEqual(zones[0].zone, "Main_Zone")
        self.assertEqual(zones[1].zone, "Zone_2")


class TestMenuCursor(unittest.TestCase):

    def _input_sel(self, input_sel):
        return ''.join(
            [
                '<YAMAHA_AV rsp="GET" RC="0"><Main_Zone><Input><Input_Sel>',
                input_sel,
                '</Input_Sel></Input></Main_Zone></YAMAHA_AV>',
            ]
        )

    @requests_mock.mock()
    def test_net_radio(self, m):
        m.get(DESC_XML, text=sample_content('rx-v675-desc.xml'))
        m.post(CTRL_URL, text=sample_content("rx-v675-inputs-resp.xml"))
        rec = rxv.RXV(CTRL_URL)

        rec.input = 'NET RADIO'
        m.post(CTRL_URL, text=self._input_sel('NET RADIO'))
        rec.menu_up()
        rec.menu_down()
        rec.menu_sel()
        rec.menu_return()
        rec.menu_return_to_home()
        self.assertIn('<List_Control>', m.last_request.text)
        with self.assertRaises(rxv.exceptions.MenuActionUnavailable):
            rec.menu_left()
        with self.assertRaises(rxv.exceptions.MenuActionUnavailable):
            rec.menu_right()

    @requests_mock.mock()
    def test_tuner(self, m):
        m.get(DESC_XML, text=sample_content('rx-v675-desc.xml'))
        m.post(CTRL_URL, text=sample_content("rx-v675-inputs-resp.xml"))
        rec = rxv.RXV(CTRL_URL)

        rec.input = 'TUNER'
        m.post(CTRL_URL, text=self._input_sel('TUNER'))
        with self.assertRaises(rxv.exceptions.MenuUnavailable):
            rec.menu_up()

    @requests_mock.mock()
    def test_hdmi(self, m):
        m.get(DESC_XML, text=sample_content('rx-v675-desc.xml'))
        m.post(CTRL_URL, text=sample_content("rx-v675-inputs-resp.xml"))
        rec = rxv.RXV(CTRL_URL)

        rec.input = 'HDMI1'
        m.post(CTRL_URL, text=self._input_sel('HDMI1'))
        rec.menu_up()
        rec.menu_down()
        rec.menu_left()
        rec.menu_right()
        rec.menu_sel()
        rec.menu_return()
        rec.menu_return_to_home()
        rec.menu_on_screen()
        rec.menu_top_menu()
        rec.menu_menu()
        rec.menu_option()
        rec.menu_display()
        self.assertIn('<Cursor_Control>', m.last_request.text)
