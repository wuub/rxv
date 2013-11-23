#!/usr/bin/env python
import rxv
import time


rx = None

def setup_module(module):
    receivers = rxv.find()
    if not receivers:
        raise RuntimeError("you'll need at least one receiver on your network")

    module.rx = receivers[0]
    module.rx.on = False
    time.sleep(1.0)


def teardown_module(module):
    module.rx.on = False


def test_on_off():
    assert rx.on == False, "reciver should be turned off"
    rx.on = True
    time.sleep(1.0)
    assert rx.on


def test_basic_status():
    bs = rx.basic_status
    assert bs.input == rx.input
    assert bs.on == 'On'


def test_inputs():
    assert rx.input in rx.inputs()
    assert "HDMI1" in rx.inputs()
    rx.input = "HDMI1"
    time.sleep(0.1)
    assert rx.input == "HDMI1"
    rx.input = "HDMI2"
    time.sleep(0.1)
    assert rx.input == "HDMI2"


def test_menu():
    rx.input = "NET RADIO"
    time.sleep(2.0)
    assert rx.menu_status()
    rx.menu_jump_line(3)
    rx.menu_up()
    rx.menu_down()


def test_fade():
    rx.volume = -50
    rx.volume_fade(-48)
    assert rx.volume == -48
    rx.volume_fade(-51)
    assert rx.volume == -51
