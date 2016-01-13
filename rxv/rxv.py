#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function

import re
import time
import requests
import warnings
import xml.etree.ElementTree as ET
from math import floor
from collections import namedtuple

from .exceptions import ResponseException, MenuUnavailable

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

BasicStatus = namedtuple("BasicStatus", "on volume mute input")
PlayStatus = namedtuple("PlayStatus", "playing artist album song")
MenuStatus = namedtuple("MenuStatus", "ready layer name current_line max_line current_list")

GetParam = 'GetParam'
YamahaCommand = '<YAMAHA_AV cmd="{command}">{payload}</YAMAHA_AV>'
MainZone = '<Main_Zone>{request_text}</Main_Zone>'
BasicStatusGet = '<Basic_Status>GetParam</Basic_Status>'
PowerControl = '<Power_Control><Power>{state}</Power></Power_Control>'
PowerControlSleep = '<Power_Control><Sleep>{sleep_value}</Sleep></Power_Control>'
Input = '<Input><Input_Sel>{input_name}</Input_Sel></Input>'
InputSelItem = '<Input><Input_Sel_Item>{input_name}</Input_Sel_Item></Input>'
ConfigGet = '<{src_name}><Config>GetParam</Config></{src_name}>'
PlayGet = '<{src_name}><Play_Info>GetParam</Play_Info></{src_name}>'
ListGet = '<{src_name}><List_Info>GetParam</List_Info></{src_name}>'
ListControlJumpLine = '<{src_name}><List_Control><Jump_Line>{lineno}</Jump_Line>' \
                      '</List_Control></{src_name}>'
ListControlCursor = '<{src_name}><List_Control><Cursor>{action}</Cursor></List_Control></{src_name}>'
VolumeLevel = '<Volume><Lvl>{value}</Lvl></Volume>'
VolumeLevelValue = '<Val>{val}</Val><Exp>{exp}</Exp><Unit>{unit}</Unit>'
VolumeMute = '<Volume><Mute>{state}</Mute></Volume>'
SelectNetRadioLine = '<NET_RADIO><List_Control><Direct_Sel>Line_{lineno}'\
                     '</Direct_Sel></List_Control></NET_RADIO>'


class RXV(object):

    def __init__(self, ctrl_url, model_name="Unknown", friendly_name='Unknown'):
        if re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}", ctrl_url):
            # backward compatibility: accept ip address as a contorl url
            warnings.warn("Using IP address as a Control URL is deprecated")
            ctrl_url = 'http://%s/YamahaRemoteControl/ctrl' % ctrl_url
        self.ctrl_url = ctrl_url
        self.model_name = model_name
        self.friendly_name = friendly_name
        self._inputs_cache = None

    def __unicode__(self):
        return u'''<{cls} model_name="{model}" ctrl_url="{ctrl_url}" at {addr}>'''.format(
            cls=self.__class__.__name__,
            model=self.model_name,
            ctrl_url=self.ctrl_url,
            addr=hex(id(self))
        )

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return self.__unicode__()

    def _request(self, command, request_text, main_zone=True):
        if main_zone:
            payload = MainZone.format(request_text=request_text)
        else:
            payload = request_text

        request_text = YamahaCommand.format(command=command, payload=payload)
        res = requests.post(
            self.ctrl_url,
            data=request_text,
            headers={"Content-Type": "text/xml"}
        )
        response = ET.XML(res.content)
        if response.get("RC") != "0":
            raise ResponseException(res.content)
        return response

    @property
    def basic_status(self):
        response = self._request('GET', BasicStatusGet)
        on = response.find("Main_Zone/Basic_Status/Power_Control/Power").text
        inp = response.find("Main_Zone/Basic_Status/Input/Input_Sel").text
        mute = response.find("Main_Zone/Basic_Status/Volume/Mute").text
        volume = response.find("Main_Zone/Basic_Status/Volume/Lvl/Val").text
        volume = int(volume) / 10.0

        status = BasicStatus(on, volume, mute, inp)
        return status

    @property
    def on(self):
        request_text = PowerControl.format(state=GetParam)
        response = self._request('GET', request_text)
        power = response.find("Main_Zone/Power_Control/Power").text
        assert power in ["On", "Standby"]
        return power == "On"

    @on.setter
    def on(self, state):
        assert state in [True, False]
        new_state = "On" if state else "Standby"
        request_text = PowerControl.format(state=new_state)
        response = self._request('PUT', request_text)
        return response

    def off(self):
        return self.on(False)

    @property
    def input(self):
        request_text = Input.format(input_name=GetParam)
        response = self._request('GET', request_text)
        return response.find("Main_Zone/Input/Input_Sel").text

    @input.setter
    def input(self, input_name):
        assert input_name in self.inputs()
        request_text = Input.format(input_name=input_name)
        self._request('PUT', request_text)

    def inputs(self):
        if not self._inputs_cache:
            request_text = InputSelItem.format(input_name=GetParam)
            res = self._request('GET', request_text)
            self._inputs_cache = dict(zip((elt.text
                                           for elt in res.iter('Param')),
                                          (elt.text
                                           for elt in res.iter("Src_Name"))))
        return self._inputs_cache

    def _src_name(self, cur_input):
        if cur_input not in self.inputs():
            return None
        return self.inputs()[cur_input]

    def is_ready(self):
        src_name = self._src_name(self.input)
        if not src_name:
            return True  # input is instantly ready

        request_text = ConfigGet.format(src_name=src_name)
        config = self._request('GET', request_text, main_zone=False)

        avail = next(config.iter('Feature_Availability'))
        return avail.text == 'Ready'

    def play_status(self):
        src_name = self._src_name(self.input)
        if not src_name:
            return None

        request_text = PlayGet.format(src_name=src_name)
        res = self._request('GET', request_text, main_zone=False)

        playing = (next(res.iter("Playback_Info")).text == "Play")
        artist = next(res.iter("Artist")).text
        album = next(res.iter("Album")).text
        song = next(res.iter("Song")).text

        status = PlayStatus(playing, artist, album, song)
        return status

    def menu_status(self):
        cur_input = self.input
        src_name = self._src_name(cur_input)
        if not src_name:
            raise MenuUnavailable(cur_input)

        request_text = ListGet.format(src_name=src_name)
        res = self._request('GET', request_text, main_zone=False)

        ready = (next(res.iter("Menu_Status")).text == "Ready")
        layer = int(next(res.iter("Menu_Layer")).text)
        name = next(res.iter("Menu_Name")).text
        current_line = int(next(res.iter("Current_Line")).text)
        max_line = int(next(res.iter("Max_Line")).text)
        current_list = next(res.iter('Current_List'))

        cl = {
            elt.tag: elt.find('Txt').text
            for elt in current_list.getchildren()
            if elt.find('Attribute').text != 'Unselectable'
        }

        status = MenuStatus(ready, layer, name, current_line, max_line, cl)
        return status

    def menu_jump_line(self, lineno):
        cur_input = self.input
        src_name = self._src_name(cur_input)
        if not src_name:
            raise MenuUnavailable(cur_input)

        request_text = ListControlJumpLine.format(src_name=src_name, lineno=lineno)
        return self._request('PUT', request_text, main_zone=False)

    def _menu_cursor(self, action):
        cur_input = self.input
        src_name = self._src_name(cur_input)
        if not src_name:
            raise MenuUnavailable(cur_input)

        request_text = ListControlCursor.format(src_name=src_name, action=action)
        return self._request('PUT', request_text, main_zone=False)

    def menu_up(self):
        return self._menu_cursor("Up")

    def menu_down(self):
        return self._menu_cursor("Down")

    def menu_left(self):
        return self._menu_cursor("Left")

    def menu_right(self):
        return self._menu_cursor("Right")

    def menu_sel(self):
        return self._menu_cursor("Sel")

    def menu_return(self):
        return self._menu_cursor("Return")

    @property
    def volume(self):
        request_text = VolumeLevel.format(value=GetParam)
        response = self._request('GET', request_text)
        vol = response.find('Main_Zone/Volume/Lvl/Val').text
        return float(vol) / 10.0

    @volume.setter
    def volume(self, value):
        value = str(int(value * 10))
        exp = 1
        unit = 'dB'

        volume_val = VolumeLevelValue.format(val=value, exp=exp, unit=unit)
        request_text = VolumeLevel.format(value=volume_val)
        self._request('PUT', request_text)

    def volume_fade(self, final_vol, sleep=0.5):
        start_vol = int(floor(self.volume))
        step = 1 if final_vol > start_vol else -1
        final_vol += step  # to make sure, we don't stop one dB before

        for val in range(start_vol, final_vol, step):
            self.volume = val
            time.sleep(sleep)

    @property
    def mute(self):
        request_text = VolumeMute.format(state=GetParam)
        response = self._request('GET', request_text)
        mute = response.find('Main_Zone/Volume/Mute').text
        assert mute in ["On", "Off"]
        return mute == "On"

    @mute.setter
    def mute(self, state):
        assert state in [True, False]
        new_state = "On" if state else "Off"
        request_text = VolumeMute.format(state=new_state)
        response = self._request('PUT', request_text)
        return response

    def _direct_sel(self, lineno):
        request_text = SelectNetRadioLine.format(lineno=lineno)
        return self._request('PUT', request_text, main_zone=False)

    @property
    def sleep(self):
        request_text = PowerControlSleep.format(sleep_value=GetParam)
        response = self._request('GET', request_text)
        sleep = response.find("Main_Zone/Power_Control/Sleep").text
        return sleep

    @sleep.setter
    def sleep(self, value):
        request_text = PowerControlSleep.format(sleep_value=value)
        self._request('PUT', request_text)

    @property
    def small_image_url(self):
        host = urlparse(self.ctrl_url).hostname
        return "http://{}:8080/BCO_device_sm_icon.png".format(host)

    @property
    def large_image_url(self):
        host = urlparse(self.ctrl_url).hostname
        return "http://{}:8080/BCO_device_lrg_icon.png".format(host)

