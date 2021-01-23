import unittest
import requests_mock
import rxv

FAKE_IP = '10.0.0.0'
DESC_XML = 'http://%s/YamahaRemoteControl/desc.xml' % FAKE_IP
CTRL_URL = 'http://%s/YamahaRemoteControl/ctrl' % FAKE_IP


def sample_content(name):
    with open('tests/samples/%s' % name) as f:
        return f.read()


class TestSurroundRXV(unittest.TestCase):

    @requests_mock.mock()
    def test_surround(self, m):
        m.get(DESC_XML, text=sample_content('rx-v473-desc.xml'))
        rec = rxv.RXV(CTRL_URL)
        surround = rec.surround_programs()
        self.assertIn("Drama", surround)
        self.assertIn("Direct", surround)
        self.assertIn("Straight", surround)

    @requests_mock.mock()
    def test_direct_available(self, m):
        # request order for CTRL_URL:
        # 1. assert "Drama" == rec.surround_program
        # 1.1 request for GET direct mode
        # 1.2 request for GET surround program
        # 2. rec.direct_mode = True
        # 2.1 request for PUT direct mode = true
        # 3. assert True == rec.direct_mode
        # 3.1 request for GET direct mode
        # 4. assert "Direct" == rec.surround_program
        # 4.1 request for GET direct mode (reuses last entry in list)
        responses = [
            {'text': sample_content("rx-v479-get-directmode-off-resp.xml")},
            {'text': sample_content("rx-v479-get-surround-program-drama-resp.xml")},
            {'text': sample_content("rx-v479-put-directmode-resp.xml")},
            {'text': sample_content("rx-v479-get-directmode-on-resp.xml")},
        ]

        m.get(DESC_XML, text=sample_content('rx-v479-desc.xml'))
        m.post(CTRL_URL, responses)

        rec = rxv.RXV(CTRL_URL)
        surround = rec.surround_programs()
        self.assertIn("Direct", surround)

        self.assertEqual("Drama", rec.surround_program)
        rec.surround_program = "Direct"
        self.assertTrue(rec.direct_mode)
        self.assertEqual("Direct", rec.surround_program)

    @requests_mock.mock()
    def test_direct_notavailable(self, m):
        m.get(DESC_XML, text=sample_content('rx-v675-desc.xml'))
        m.post(CTRL_URL, text=sample_content("rx-v675-get-surround-program-drama-resp.xml"))
        rec = rxv.RXV(CTRL_URL)
        surround = rec.surround_programs()
        self.assertNotIn("Direct", surround)
        self.assertEqual("Drama", rec.surround_program)
        self.assertFalse(rec.direct_mode)
        with self.assertRaises(AssertionError):
            rec.direct_mode = True
