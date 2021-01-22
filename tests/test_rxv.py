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
        m.post(CTRL_URL, text=sample_content('rx-v675-inputs-resp.xml'))
        rec = rxv.RXV(CTRL_URL)

        rec.input = 'NET RADIO'
        m.post(CTRL_URL, text=self._input_sel('NET RADIO'))

        rec.menu_up()
        self.assertIn(f'>{rxv.rxv.CURSOR_UP}<', m.last_request.text)
        self.assertIn('<List_Control>', m.last_request.text)

        rec.menu_down()
        self.assertIn(f'>{rxv.rxv.CURSOR_DOWN}<', m.last_request.text)
        self.assertIn('<List_Control>', m.last_request.text)

        rec.menu_sel()
        self.assertIn(f'>{rxv.rxv.CURSOR_SEL}<', m.last_request.text)
        self.assertIn('<List_Control>', m.last_request.text)

        rec.menu_return()
        self.assertIn(f'>{rxv.rxv.CURSOR_RETURN}<', m.last_request.text)
        self.assertIn('<List_Control>', m.last_request.text)

        rec.menu_return_to_home()
        self.assertIn(f'>{rxv.rxv.CURSOR_RETURN_TO_HOME}<', m.last_request.text)
        self.assertIn('<List_Control>', m.last_request.text)

        with self.assertRaises(rxv.exceptions.MenuActionUnavailable):
            rec.menu_left()
        with self.assertRaises(rxv.exceptions.MenuActionUnavailable):
            rec.menu_right()
        with self.assertRaises(rxv.exceptions.MenuActionUnavailable):
            rec.menu_on_screen()
        with self.assertRaises(rxv.exceptions.MenuActionUnavailable):
            rec.menu_top_menu()
        with self.assertRaises(rxv.exceptions.MenuActionUnavailable):
            rec.menu_menu()
        with self.assertRaises(rxv.exceptions.MenuActionUnavailable):
            rec.menu_option()
        with self.assertRaises(rxv.exceptions.MenuActionUnavailable):
            rec.menu_display()

    @requests_mock.mock()
    def test_tuner(self, m):
        m.get(DESC_XML, text=sample_content('rx-v675-desc.xml'))
        m.post(CTRL_URL, text=sample_content('rx-v675-inputs-resp.xml'))
        rec = rxv.RXV(CTRL_URL)

        rec.input = 'TUNER'
        m.post(CTRL_URL, text=self._input_sel('TUNER'))
        with self.assertRaises(rxv.exceptions.MenuUnavailable):
            rec.menu_up()

    @requests_mock.mock()
    def test_hdmi(self, m):
        m.get(DESC_XML, text=sample_content('rx-v675-desc.xml'))
        m.post(CTRL_URL, text=sample_content('rx-v675-inputs-resp.xml'))
        rec = rxv.RXV(CTRL_URL)

        rec.input = 'HDMI1'
        m.post(CTRL_URL, text=self._input_sel('HDMI1'))

        rec.menu_up()
        self.assertIn(f'>{rxv.rxv.CURSOR_UP}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_down()
        self.assertIn(f'>{rxv.rxv.CURSOR_DOWN}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_left()
        self.assertIn(f'>{rxv.rxv.CURSOR_LEFT}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_right()
        self.assertIn(f'>{rxv.rxv.CURSOR_RIGHT}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_sel()
        self.assertIn(f'>{rxv.rxv.CURSOR_SEL}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_return()
        self.assertIn(f'>{rxv.rxv.CURSOR_RETURN}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_return_to_home()
        self.assertIn(f'>{rxv.rxv.CURSOR_RETURN_TO_HOME}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_on_screen()
        self.assertIn(f'>{rxv.rxv.CURSOR_ON_SCREEN}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_top_menu()
        self.assertIn(f'>{rxv.rxv.CURSOR_TOP_MENU}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_menu()
        self.assertIn(f'>{rxv.rxv.CURSOR_MENU}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_option()
        self.assertIn(f'>{rxv.rxv.CURSOR_OPTION}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)

        rec.menu_display()
        self.assertIn(f'>{rxv.rxv.CURSOR_DISPLAY}<', m.last_request.text)
        self.assertIn('<Cursor_Control>', m.last_request.text)
