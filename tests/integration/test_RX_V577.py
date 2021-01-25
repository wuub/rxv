"""Integration test for the RX-V577 model receiver."""
import pytest

import rxv


@pytest.fixture
def rx(vcr):
    with vcr.use_cassette('RX-V577.yaml'):
        return rxv.RXV(
            'http://192.168.1.100:80/YamahaRemoteControl/ctrl', 'RX-V577'
        )


@pytest.mark.vcr()
def test_on_off(rx):
    assert rx.on is False, "reciver should be turned off"
    rx.on = True
    assert rx.on


@pytest.mark.vcr()
def test_basic_status(rx):
    bs = rx.basic_status
    assert bs.input == rx.input
    assert bs.on == 'On'


@pytest.mark.vcr()
def test_inputs(rx):
    assert rx.input in rx.inputs()
    assert "HDMI1" in rx.inputs()
    rx.input = "HDMI1"
    assert rx.input == "HDMI1"
    rx.input = "HDMI2"
    assert rx.input == "HDMI2"


@pytest.mark.vcr()
def test_menu(rx):
    rx.input = "NET RADIO"
    assert rx.menu_status()
    rx.menu_jump_line(3)
    rx.menu_up()
    rx.menu_down()

    rx.input = "HDMI1"
    rx.menu_right()
    rx.menu_left()


@pytest.mark.vcr()
def test_fade(rx):
    rx.volume = -50
    rx.volume_fade(-48)
    assert rx.volume == -48
    rx.volume_fade(-51)
    assert rx.volume == -51
