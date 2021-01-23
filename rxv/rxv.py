#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import copy
import logging
import re
import time
import warnings
import xml
from collections import namedtuple
from math import floor

import requests
from defusedxml import cElementTree

from .exceptions import (CommandUnavailable, MenuUnavailable,
                         MenuActionUnavailable, PlaybackUnavailable,
                         ResponseException, UnknownPort)

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

logger = logging.getLogger('rxv')


class PlaybackSupport:
    """Container for Playback support.

    This stores a set of booleans so that they are easy to turn into
    whatever format the support needs to be specified at a higher
    level.

    """
    def __init__(self, play=False, stop=False, pause=False,
                 skip_f=False, skip_r=False):
        self.play = play
        self.stop = stop
        self.pause = pause
        self.skip_f = skip_f
        self.skip_r = skip_r


BasicStatus = namedtuple("BasicStatus", "on volume mute input")
PlayStatus = namedtuple("PlayStatus", "playing artist album song station")
MenuStatus = namedtuple("MenuStatus", "ready layer name current_line max_line current_list")

GetParam = 'GetParam'
YamahaCommand = '<YAMAHA_AV cmd="{command}">{payload}</YAMAHA_AV>'
Zone = '<{zone}>{request_text}</{zone}>'
BasicStatusGet = '<Basic_Status>GetParam</Basic_Status>'
PartyMode = '<System><Party_Mode><Mode>{state}</Mode></Party_Mode></System>'
PowerControl = '<Power_Control><Power>{state}</Power></Power_Control>'
PowerControlSleep = '<Power_Control><Sleep>{sleep_value}</Sleep></Power_Control>'
Input = '<Input><Input_Sel>{input_name}</Input_Sel></Input>'
InputSelItem = '<Input><Input_Sel_Item>{input_name}</Input_Sel_Item></Input>'
ConfigGet = '<{src_name}><Config>GetParam</Config></{src_name}>'
PlayGet = '<{src_name}><Play_Info>GetParam</Play_Info></{src_name}>'
PlayControl = '<{src_name}><Play_Control><Playback>{action}</Playback></Play_Control></{src_name}>'
ListGet = '<{src_name}><List_Info>GetParam</List_Info></{src_name}>'
ListControlJumpLine = '<{src_name}><List_Control><Jump_Line>{lineno}</Jump_Line>' \
                      '</List_Control></{src_name}>'
ListControlCursor = '<{src_name}><List_Control><Cursor>{action}</Cursor>'\
                    '</List_Control></{src_name}>'
CursorControlCursor = '<{src_name}><Cursor_Control><Cursor>{action}</Cursor>'\
                      '</Cursor_Control></{src_name}>'
VolumeLevel = '<Volume><Lvl>{value}</Lvl></Volume>'
VolumeLevelValue = '<Val>{val}</Val><Exp>{exp}</Exp><Unit>{unit}</Unit>'
VolumeMute = '<Volume><Mute>{state}</Mute></Volume>'
SoundVideo = '<Sound_Video>{value}</Sound_Video>'
SelectNetRadioLine = '<NET_RADIO><List_Control><Direct_Sel>Line_{lineno}'\
                     '</Direct_Sel></List_Control></NET_RADIO>'
SelectServerLine = '<SERVER><List_Control><Direct_Sel>Line_{lineno}'\
                   '</Direct_Sel></List_Control></SERVER>'

HdmiOut = '<System><Sound_Video><HDMI><Output><OUT_{port}>{command}</OUT_{port}>'\
          '</Output></HDMI></Sound_Video></System>'
AvailableScenes = '<Config>GetParam</Config>'
Scene = '<Scene><Scene_Sel>{parameter}</Scene_Sel></Scene>'
SurroundProgram = '<Surround><Program_Sel><Current>{parameter}</Current></Program_Sel></Surround>'
DirectMode = '<Sound_Video><Direct>{parameter}</Direct></Sound_Video>'

# String constants
STRAIGHT = "Straight"
DIRECT = "Direct"

# PlayStatus options
ARTIST_OPTIONS = ["Artist", "Program_Type"]
ALBUM_OPTIONS = ["Album", "Radio_Text_A"]
SONG_OPTIONS = ["Song", "Track", "Radio_Text_B"]
STATION_OPTIONS = ["Station", "Program_Service"]

# Cursor commands.
CURSOR_DISPLAY = "Display"
CURSOR_DOWN = "Down"
CURSOR_LEFT = "Left"
CURSOR_MENU = "Menu"
CURSOR_ON_SCREEN = "On Screen"
CURSOR_OPTION = "Option"
CURSOR_SEL = "Sel"
CURSOR_RETURN = "Return"
CURSOR_RETURN_TO_HOME = "Return to Home"
CURSOR_RIGHT = "Right"
CURSOR_TOP_MENU = "Top Menu"
CURSOR_UP = "Up"


class RXV(object):

    def __init__(self, ctrl_url, model_name="Unknown",
                 serial_number=None, zone="Main_Zone",
                 friendly_name='Unknown', unit_desc_url=None,
                 http_timeout=10.0):
        if re.match(r"\d{1,3}\.\d{1,3}\.\d{1,3}.\d{1,3}", ctrl_url):
            # backward compatibility: accept ip address as a contorl url
            warnings.warn("Using IP address as a Control URL is deprecated")
            ctrl_url = 'http://%s/YamahaRemoteControl/ctrl' % ctrl_url
        self.ctrl_url = ctrl_url
        self.unit_desc_url = unit_desc_url or re.sub('ctrl$', 'desc.xml', ctrl_url)
        self.model_name = model_name
        self.serial_number = serial_number
        self.friendly_name = friendly_name
        self.http_timeout = http_timeout
        self._inputs_cache = None
        self._zones_cache = None
        self._zone = zone
        self._surround_programs_cache = None
        self._scenes_cache = None
        self._session = requests.Session()
        self._discover_features()

    def _discover_features(self):
        """Pull and parse the desc.xml so we can query it later."""
        try:
            desc_xml = self._session.get(
                self.unit_desc_url, timeout=self.http_timeout
            ).content
            if not desc_xml:
                logger.error(
                    "Unsupported Yamaha device? Failed to fetch {}".format(
                        self.unit_desc_url
                    ))
                return
            self._desc_xml = cElementTree.fromstring(desc_xml)
        except xml.etree.ElementTree.ParseError:
            logger.exception("Invalid XML returned for request %s: %s",
                             self.unit_desc_url, desc_xml)
            raise
        except Exception:
            logger.exception("Failed to fetch %s" % self.unit_desc_url)
            raise

    def __unicode__(self):
        return (f'<{self.__class__.__name__} '
                f'model_name="{self.model_name}" '
                f'serial_number="{self.serial_number}" '
                f'zone="{self._zone}" '
                f'ctrl_url="{self.ctrl_url}" '
                f'at {hex(id(self))}>')

    def __str__(self):
        return self.__unicode__()

    def __repr__(self):
        return self.__unicode__()

    def _request(self, command, request_text, zone_cmd=True):
        if zone_cmd:
            payload = Zone.format(request_text=request_text, zone=self._zone)
        else:
            payload = request_text

        request_text = YamahaCommand.format(command=command, payload=payload)
        try:
            res = self._session.post(
                self.ctrl_url,
                data=request_text,
                headers={"Content-Type": "text/xml"},
                timeout=self.http_timeout
            )
            # releases connection to the pool
            response = cElementTree.XML(res.content)
            if response.get("RC") != "0":
                logger.error("Request %s failed with %s",
                             request_text, res.content)
                raise ResponseException(res.content)
            return response
        except xml.etree.ElementTree.ParseError:
            logger.exception("Invalid XML returned for request %s: %s",
                             request_text, res.content)
            raise

    @property
    def basic_status(self):
        response = self._request('GET', BasicStatusGet)
        on = response.find("%s/Basic_Status/Power_Control/Power" % self.zone).text
        inp = response.find("%s/Basic_Status/Input/Input_Sel" % self.zone).text
        mute = response.find("%s/Basic_Status/Volume/Mute" % self.zone).text
        volume = response.find("%s/Basic_Status/Volume/Lvl/Val" % self.zone).text
        volume = int(volume) / 10.0

        status = BasicStatus(on, volume, mute, inp)
        return status

    @property
    def on(self):
        request_text = PowerControl.format(state=GetParam)
        response = self._request('GET', request_text)
        power = response.find("%s/Power_Control/Power" % self._zone).text
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

    def get_playback_support(self, input_source=None):
        """Get playback support as bit vector.

        In order to expose features correctly in Home Assistant, we
        need to make it possible to understand what play operations a
        source supports. This builds us a Home Assistant compatible
        bit vector from the desc.xml for the specified source.
        """

        if input_source is None:
            input_source = self.input
        src_name = self._src_name(input_source)

        return PlaybackSupport(
            play=self.supports_play_method(src_name, 'Play'),
            pause=self.supports_play_method(src_name, 'Pause'),
            stop=self.supports_play_method(src_name, 'Stop'),
            skip_f=self.supports_play_method(src_name, 'Skip Fwd'),
            skip_r=self.supports_play_method(src_name, 'Skip Rev'))

    def is_playback_supported(self, input_source=None):
        if input_source is None:
            input_source = self.input
        support = self.get_playback_support(input_source)
        return support.play

    def play(self):
        self._playback_control('Play')

    def pause(self):
        self._playback_control('Pause')

    def stop(self):
        self._playback_control('Stop')

    def next(self):
        self._playback_control('Skip Fwd')

    def previous(self):
        self._playback_control('Skip Rev')

    def _playback_control(self, action):
        # Cache current input to "save" one HTTP-request
        input_source = self.input
        if not self.is_playback_supported(input_source):
            raise PlaybackUnavailable(input_source, action)

        src_name = self._src_name(input_source)
        if not src_name:
            return None

        request_text = PlayControl.format(src_name=src_name, action=action)
        response = self._request('PUT', request_text, zone_cmd=False)
        return response

    @property
    def input(self):
        request_text = Input.format(input_name=GetParam)
        response = self._request('GET', request_text)
        return response.find("%s/Input/Input_Sel" % self.zone).text

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

    @property
    def outputs(self):
        outputs = {}

        for cmd in self._find_commands('System,Sound_Video,HDMI,Output'):
            # An output typically looks like this:
            #   System,Sound_Video,HDMI,Output,OUT_1
            # Extract the index number at the end as it is needed when
            # requesting its current state.
            m = re.match(r'.*_(\d+)$', cmd)
            if m is None:
                continue

            port_number = m.group(1)
            request = HdmiOut.format(port=port_number, command='GetParam')
            response = self._request('GET', request, zone_cmd=False)
            port_state = response.find(cmd.replace(',', '/')).text.lower()
            outputs['hdmi' + str(port_number)] = port_state

        return outputs

    def enable_output(self, port, enabled):
        m = re.match(r'hdmi(\d+)', port.lower())
        if m is None:
            raise UnknownPort(port)

        request = HdmiOut.format(port=m.group(1),
                                 command='On' if enabled else 'Off')
        self._request('PUT', request, zone_cmd=False)

    def _find_commands(self, cmd_name):
        for cmd in self._desc_xml.findall('.//Cmd_List/Define'):
            if cmd.text.startswith(cmd_name):
                yield cmd.text

    @property
    def direct_mode(self):
        """
        Current state of direct mode.
        """
        if DIRECT not in self.surround_programs():
            return False

        request_text = DirectMode.format(parameter="<Mode>GetParam</Mode>")
        response = self._request('GET', request_text)
        direct = response.find(
            "%s/Sound_Video/Direct/Mode" % self.zone
        ).text == "On"

        return direct

    @direct_mode.setter
    def direct_mode(self, on):
        """
        Enable/Disable direct mode.

        Precondition: DIRECT mode is supported, raises AssertionError otherwise.
        """
        assert DIRECT in self.surround_programs()
        if on:
            request_text = DirectMode.format(parameter="<Mode>On</Mode>")
        else:
            request_text = DirectMode.format(parameter="<Mode>Off</Mode>")
        self._request('PUT', request_text)

    @property
    def surround_program(self):
        """
        Get current selected surround program.

        If a STRAIGHT or DIRECT mode is supported and active, returns that mode.
        Otherwise returns the currently active surround program.
        """
        if self.direct_mode:
            return DIRECT

        request_text = SurroundProgram.format(parameter=GetParam)
        response = self._request('GET', request_text)
        straight = response.find(
            "%s/Surround/Program_Sel/Current/Straight" % self.zone
        ).text == "On"

        if straight:
            return STRAIGHT

        program = response.find(
            "%s/Surround/Program_Sel/Current/Sound_Program" % self.zone
        ).text

        return program

    @surround_program.setter
    def surround_program(self, surround_name):
        assert surround_name in self.surround_programs()

        # short circut on direct program
        if surround_name == DIRECT:
            self.direct_mode = True
            return

        if self.direct_mode:
            # Disable direct mode before changing any other settings,
            # otherwise they don't have an effect
            self.direct_mode = False

        if surround_name == STRAIGHT:
            parameter = "<Straight>On</Straight>"
        else:
            parameter = "<Sound_Program>{parameter}</Sound_Program>".format(
                parameter=surround_name
            )
        request_text = SurroundProgram.format(parameter=parameter)
        self._request('PUT', request_text)

    def surround_programs(self):
        if not self._surround_programs_cache:
            source_xml = self._desc_xml.find(
                './/*[@YNC_Tag="%s"]' % self._zone
            )
            if source_xml is None:
                return False

            setup = source_xml.find('.//Menu[@Title_1="Setup"]')
            if setup is None:
                return False

            programs = setup.find('.//*[@Title_1="Program"]/Put_2/Param_1')
            if programs is None:
                return False

            supports = programs.findall('.//Direct')
            self._surround_programs_cache = list()
            for s in supports:
                self._surround_programs_cache.append(s.text)

            straight = setup.find('.//*[@Title_1="Straight"]/Put_1')
            if straight is not None:
                self._surround_programs_cache.append(STRAIGHT)

            direct = setup.find('.//*[@Title_1="Direct"]/Put_1')
            if direct is not None:
                self._surround_programs_cache.append(DIRECT)

        return self._surround_programs_cache

    @property
    def scene(self):
        request_text = Scene.format(parameter=GetParam)
        response = self._request('GET', request_text)
        return response.find("%s/Scene/Scene_Sel" % self.zone).text

    @scene.setter
    def scene(self, scene_name):
        assert scene_name in self.scenes()
        scene_number = self._scenes_cache.get(scene_name)
        request_text = Scene.format(parameter=scene_number)
        self._request('PUT', request_text)

    def scenes(self):
        if not self._scenes_cache:
            res = self._request('GET', AvailableScenes)
            scenes = res.find('.//Scene')
            if scenes is None:
                return False

            self._scenes_cache = {}
            for scene in scenes:
                self._scenes_cache[scene.text] = scene.tag.replace("_", " ")
        return self._scenes_cache

    @property
    def zone(self):
        return self._zone

    @zone.setter
    def zone(self, zone_name):
        assert zone_name in self.zones()
        self._zone = zone_name

    def zones(self):
        if self._zones_cache is None:
            xml = self._desc_xml
            self._zones_cache = [
                e.get("YNC_Tag") for e in xml.findall('.//*[@Func="Subunit"]')
            ]
        return self._zones_cache

    def zone_controllers(self):
        """Return separate RXV controller for each available zone."""
        controllers = []
        for zone in self.zones():
            zone_ctrl = copy.copy(self)
            zone_ctrl.zone = zone
            controllers.append(zone_ctrl)
        return controllers

    def supports_method(self, source, *args):
        # if there was a complete xpath implementation we could do
        # this all with xpath, but without it it's lots of
        # iteration. This is probably not worth optimizing, these
        # loops are cheep in the long run.
        commands = self._desc_xml.findall('.//Cmd_List')
        for c in commands:
            for item in c:
                parts = item.text.split(",")
                if parts[0] == source and parts[1:] == list(args):
                    return True
        return False

    def supports_play_method(self, source, method):
        # if there was a complete xpath implementation we could do
        # this all with xpath, but without it it's lots of
        # iteration. This is probably not worth optimizing, these
        # loops are cheep in the long run.
        source_xml = self._desc_xml.find('.//*[@YNC_Tag="%s"]' % source)
        if source_xml is None:
            return False

        play_control = source_xml.find('.//*[@Func="Play_Control"]')
        if play_control is None:
            return False

        # built in Element Tree does not support search by text()
        supports = play_control.findall('.//Put_1')
        for s in supports:
            if s.text == method:
                return True
        return False

    def _src_name(self, cur_input):
        if cur_input not in self.inputs():
            return None
        if cur_input.upper().startswith('HDMI'):
            # CEC commands can be sent over the HDMI inputs to control devices
            # connected to the receiver. These can support play methods as well
            # as menu cursor commands. Return the zone so these features
            # will be enabled.
            return self.zone
        return self.inputs()[cur_input]

    def is_ready(self):
        src_name = self._src_name(self.input)
        if not src_name:
            return True  # input is instantly ready

        request_text = ConfigGet.format(src_name=src_name)
        config = self._request('GET', request_text, zone_cmd=False)

        avail = next(config.iter('Feature_Availability'))
        return avail.text == 'Ready'

    @staticmethod
    def safe_get(doc, names):
        try:
            # python 3.x
            import html
        except ImportError:
            # python 2.7
            import HTMLParser
            html = HTMLParser.HTMLParser()

        for name in names:
            tag = doc.find(".//%s" % name)
            if tag is not None and tag.text is not None:
                # Tuner and Net Radio sometimes respond
                # with escaped entities
                return html.unescape(tag.text).strip()
        return ""

    def play_status(self):

        src_name = self._src_name(self.input)

        if not src_name:
            return None

        if not self.supports_method(src_name, 'Play_Info'):
            return

        request_text = PlayGet.format(src_name=src_name)
        res = self._request('GET', request_text, zone_cmd=False)

        playing = RXV.safe_get(res, ["Playback_Info"]) == "Play" \
            or src_name == "Tuner"

        status = PlayStatus(
            playing,
            artist=RXV.safe_get(res, ARTIST_OPTIONS),
            album=RXV.safe_get(res, ALBUM_OPTIONS),
            song=RXV.safe_get(res, SONG_OPTIONS),
            station=RXV.safe_get(res, STATION_OPTIONS)
        )
        return status

    def menu_status(self):
        cur_input = self.input
        src_name = self._src_name(cur_input)
        if not src_name:
            raise MenuUnavailable(cur_input)

        request_text = ListGet.format(src_name=src_name)
        res = self._request('GET', request_text, zone_cmd=False)

        ready = (next(res.iter("Menu_Status")).text == "Ready")
        layer = int(next(res.iter("Menu_Layer")).text)
        name = next(res.iter("Menu_Name")).text
        current_line = int(next(res.iter("Current_Line")).text)
        max_line = int(next(res.iter("Max_Line")).text)
        current_list = next(res.iter('Current_List'))

        cl = {
            elt.tag: elt.find('Txt').text
            for elt in list(current_list)
            if elt.find('Attribute').text != 'Unselectable'
        }

        status = MenuStatus(ready, layer, name, current_line, max_line, cl)
        return status

    def menu_jump_line(self, lineno):
        cur_input = self.input
        src_name = self._src_name(cur_input)
        if not src_name:
            raise MenuUnavailable(cur_input)

        request_text = ListControlJumpLine.format(
            src_name=src_name,
            lineno=lineno
        )
        return self._request('PUT', request_text, zone_cmd=False)

    def supported_cursor_actions(self, cur_input=None):
        if cur_input is None:
            cur_input = self.input
        src_name = self._src_name(cur_input)
        if not src_name:
            return frozenset()
        cursor_actions = self._desc_xml.findall(
            f'.//*[@YNC_Tag="{src_name}"]//Menu[@Func="Cursor"]/Put_1')
        if cursor_actions is None:
            return frozenset()
        return frozenset(action.text for action in cursor_actions)

    def _menu_cursor(self, action):
        cur_input = self.input
        src_name = self._src_name(cur_input)
        if not src_name:
            raise MenuUnavailable(cur_input)

        if self.supports_method(src_name, 'List_Control', 'Cursor'):
            template = ListControlCursor
        elif self.supports_method(src_name, 'Cursor_Control', 'Cursor'):
            template = CursorControlCursor
        else:
            raise MenuUnavailable(cur_input)

        # Check that the specific action is available for the input.
        if action not in self.supported_cursor_actions():
            raise MenuActionUnavailable(cur_input, action)

        request_text = template.format(
            src_name=src_name,
            action=action
        )
        return self._request('PUT', request_text, zone_cmd=False)

    def menu_up(self):
        return self._menu_cursor(CURSOR_UP)

    def menu_down(self):
        return self._menu_cursor(CURSOR_DOWN)

    def menu_left(self):
        return self._menu_cursor(CURSOR_LEFT)

    def menu_right(self):
        return self._menu_cursor(CURSOR_RIGHT)

    def menu_sel(self):
        return self._menu_cursor(CURSOR_SEL)

    def menu_return(self):
        return self._menu_cursor(CURSOR_RETURN)

    def menu_return_to_home(self):
        return self._menu_cursor(CURSOR_RETURN_TO_HOME)

    def menu_on_screen(self):
        return self._menu_cursor(CURSOR_ON_SCREEN)

    def menu_top_menu(self):
        return self._menu_cursor(CURSOR_TOP_MENU)

    def menu_menu(self):
        return self._menu_cursor(CURSOR_MENU)

    def menu_option(self):
        return self._menu_cursor(CURSOR_OPTION)

    def menu_display(self):
        return self._menu_cursor(CURSOR_DISPLAY)

    def menu_reset(self):
        while self.menu_status().layer > 1:
            self.menu_return()

    @property
    def volume(self):
        request_text = VolumeLevel.format(value=GetParam)
        response = self._request('GET', request_text)
        vol = response.find('%s/Volume/Lvl/Val' % self.zone).text
        return float(vol) / 10.0

    @volume.setter
    def volume(self, value):
        """Convert volume for setting.

        We're passing around volume in standard db units, like -52.0
        db. The API takes int values. However, the API also only takes
        int values that corespond to half db steps (so -52.0 and -51.5
        are valid, -51.8 is not).

        Through the power of math doing the int of * 2, then * 5 will
        ensure we only get half steps.
        """
        value = str(int(value * 2) * 5)
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
    def partymode(self):
        request_text = PartyMode.format(state=GetParam)
        response = self._request('GET', request_text, False)
        pmode = response.find('System/Party_Mode/Mode').text
        assert pmode in ["On", "Off"]
        return pmode == "On"

    @partymode.setter
    def partymode(self, state):
        assert state in [True, False]
        new_state = "On" if state else "Off"
        request_text = PartyMode.format(state=new_state)
        response = self._request('PUT', request_text, False)
        return response

    @property
    def mute(self):
        request_text = VolumeMute.format(state=GetParam)
        response = self._request('GET', request_text)
        mute = response.find('%s/Volume/Mute' % self.zone).text
        assert mute in ["On", "Off"]
        return mute == "On"

    @mute.setter
    def mute(self, state):
        assert state in [True, False]
        new_state = "On" if state else "Off"
        request_text = VolumeMute.format(state=new_state)
        response = self._request('PUT', request_text)
        return response

    @property
    def adaptive_drc(self):
        """
        View the current Adaptive Dynamic Range Compression setting, a means
        of equalizing various input levels at low volume. This feature is ideal
        for watching late at night (to avoid extremes of volume between
        dialogue scenes and explosions etc.) or in noisy environments. It is
        best disabled for the full dynamic range audio experience.

        :return: True if Dynamic Range Compression is enabled.
        """
        get_tag = '<Adaptive_DRC>GetParam</Adaptive_DRC>'
        request_text = SoundVideo.format(value=get_tag)
        response = self._request('GET', request_text)
        drc = response.find('%s/Sound_Video/Adaptive_DRC' % self.zone).text
        return False if drc == 'Off' else True

    @adaptive_drc.setter
    def adaptive_drc(self, value=False):
        """
        :param value: True to enable dynamic range compression. Default False.
        """
        set_value = 'Auto' if value else 'Off'
        set_tag = '<Adaptive_DRC>{}</Adaptive_DRC>'.format(set_value)
        request_text = SoundVideo.format(value=set_tag)
        self._request('PUT', request_text)

    @property
    def dialogue_level(self):
        """
        An adjustment to elevate the volume of dialogue sounds; useful if the
        volume of dialogue is difficult to make out against background sounds
        or music.

        :return: An integer between 0 (no adjustment) to 3 (most increased).
        """
        if self.supports_method(self.zone, "Sound_Video", "Dialogue_Adjust", "Dialogue_Lvl"):
            raise CommandUnavailable(self.zone, "Dialogue_Lvl")

        get_tag = '<Dialogue_Adjust><Dialogue_Lvl>GetParam' \
                  '</Dialogue_Lvl></Dialogue_Adjust>'
        request_text = SoundVideo.format(value=get_tag)
        response = self._request('GET', request_text)
        level = response.find('%s/Sound_Video/Dialogue_Adjust/Dialogue_Lvl'
                              % self.zone).text
        return int(level)

    @dialogue_level.setter
    def dialogue_level(self, value=0):
        """
        :param value: An integer between 0 and 3 to determine how much to
            increase dialogue sounds over other sounds. A value of zero
            disables this feature.
        """
        if self.supports_method(self.zone, "Sound_Video", "Dialogue_Adjust", "Dialogue_Lvl"):
            raise CommandUnavailable(self.zone, "Dialogue_Lvl")

        if int(value) not in [0, 1, 2, 3]:
            raise ValueError("Value must be 0, 1, 2, or 3")
        set_tag = '<Dialogue_Adjust><Dialogue_Lvl>{}' \
                  '</Dialogue_Lvl></Dialogue_Adjust>'.format(int(value))
        request_text = SoundVideo.format(value=set_tag)
        self._request('PUT', request_text)

    def _direct_sel(self, lineno):
        request_text = SelectNetRadioLine.format(lineno=lineno)
        return self._request('PUT', request_text, zone_cmd=False)

    def net_radio(self, path):
        """Play net radio at the specified path.

        This lets you play a NET_RADIO address in a single command
        with by encoding it with > as separators. For instance:

            Bookmarks>Internet>Radio Paradise

        It does this by push commands, then looping and making sure
        the menu is in a ready state before we try to push the next
        one. A sufficient number of iterations are allowed for to
        ensure we give it time to get there.

        TODO: better error handling if we some how time out
        TODO: multi page menus (scrolling down)
        """
        layers = path.split(">")
        self.input = "NET RADIO"
        self.menu_reset()

        for attempt in range(20):
            menu = self.menu_status()
            if menu.ready:
                for line, value in menu.current_list.items():
                    if value == layers[menu.layer - 1]:
                        lineno = line[5:]
                        self._direct_sel(lineno)
                        if menu.layer == len(layers):
                            return
                        break
            else:
                # print("Sleeping because we are not ready yet")
                time.sleep(1)

    def _direct_sel_server(self, lineno):
        request_text = SelectServerLine.format(lineno=lineno)
        return self._request('PUT', request_text, zone_cmd=False)

    def server(self, path):
        """Play from specified server

        This lets you play a SERVER address in a single command
        with by encoding it with > as separators. For instance:

            Server>Playlists>GoodVibes

        This code is copied from the net_radio function.

        TODO: better error handling if we some how time out
        """
        layers = path.split(">")
        self.input = "SERVER"

        for attempt in range(20):
            menu = self.menu_status()
            if menu.ready:
                for line, value in menu.current_list.items():
                    if value == layers[menu.layer - 1]:
                        lineno = line[5:]
                        self._direct_sel_server(lineno)
                        if menu.layer == len(layers):
                            return
                        break
            else:
                # print("Sleeping because we are not ready yet")
                time.sleep(1)

    @property
    def sleep(self):
        request_text = PowerControlSleep.format(sleep_value=GetParam)
        response = self._request('GET', request_text)
        sleep = response.find("%s/Power_Control/Sleep" % self._zone).text
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
