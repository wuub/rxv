import testtools
import requests_mock
import rxv

FAKE_IP = '10.0.0.0'
DESC_XML = 'http://%s/YamahaRemoteControl/desc.xml' % FAKE_IP


def sample_content(name):
    with open('tests/samples/%s' % name) as f:
        return f.read()


class TestSurroundRXV(testtools.TestCase):

    @requests_mock.mock()
    def test_surround(self, m):
        m.get(DESC_XML, text=sample_content('rx-v473-desc.xml'))
        rec = rxv.RXV(FAKE_IP)
        surround = rec.surround_programs()
        self.assertIn("Drama", surround)
