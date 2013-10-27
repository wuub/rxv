import time
import requests
import xml.etree.ElementTree as ET
from math import floor
from collections import namedtuple


BasicStatus = namedtuple("BasicStatus", "on volume mute input")
MenuStatus = namedtuple("MenuStatus",
                        "ready layer name current_line max_line current_list")

YamahaCommand = '<YAMAHA_AV cmd="%s">%s</YAMAHA_AV>'
MainZone = '<Main_Zone>%s</Main_Zone>'
BasicStatusGet = '<Basic_Status>GetParam</Basic_Status>'
PowerControl = '<Power_Control><Power>%s</Power></Power_Control>'
PowerControlSleep = '<Power_Control><Sleep>%s</Sleep></Power_Control>'
Input = '<Input><Input_Sel>%s</Input_Sel></Input>'
InputSelItem = '<Input><Input_Sel_Item>%s</Input_Sel_Item></Input>'
ConfigGet = '<%s><Config>GetParam</Config></%s>'
ListGet = '<%s><List_Info>GetParam</List_Info></%s>'
ListControlJumpLine = '<%s><List_Control><Jump_Line>%s</Jump_Line>' \
                      '</List_Control></%s>'
ListControlCursor = '<%s><List_Control><Cursor>%s</Cursor></List_Control></%s>'
VolumeLevel = '<Volume><Lvl>%s</Lvl></Volume>'
VolumeLevelSet = VolumeLevel % '<Val>%s</Val><Exp>%s</Exp><Unit>%s</Unit>'
SelectNetRadioLine = '<NET_RADIO><List_Control><Direct_Sel>Line_%s'\
                     '</Direct_Sel></List_Control></NET_RADIO>'


class RXV473(object):

    def __init__(self, ip):
        self._ip = ip
        self._inputs_cache = None

    @property
    def ctrl_url(self):
        return 'http://%s/YamahaRemoteControl/ctrl' % self._ip

    def _request(self, command, request_text, main_zone=True):
        inner_text = MainZone % request_text if main_zone else request_text
        request_text = (YamahaCommand % (command, inner_text))
        res = requests.post(self.ctrl_url,
                            data=request_text,
                            headers={"Content-Type": "text/xml"})
        response = ET.XML(res.content)
        assert response.get("RC") == "0"
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
        request_text = PowerControl % 'GetParam'
        response = self._request('GET', request_text)
        power = response.find("Main_Zone/Power_Control/Power").text
        assert power in ["On", "Standby"]
        return power == "On"

    @on.setter
    def on(self, state):
        assert state in [True, False]
        new_state = "On" if state else "Standby"
        request_text = PowerControl % new_state
        response = self._request('PUT', request_text)
        return response

    def off(self):
        return self.on(False)

    @property
    def input(self):
        request_text = Input % 'GetParam'
        response = self._request(request_text)
        return response.find("Main_Zone/Input/Input_Sel").text

    @input.setter
    def input(self, input_name):
        assert input_name in self.inputs()
        request_text = Input % input_name
        self._request('PUT', request_text)

    def inputs(self):
        if not self._inputs_cache:
            request_text = InputSelItem % 'GetParam'
            res = self._request('GET', request_text)
            self._inputs_cache = dict(zip((elt.text
                                           for elt in res.iter('Param')),
                                          (elt.text
                                           for elt in res.iter("Src_Name"))))
        return self._inputs_cache

    def is_ready(self):
        if self.input not in self.inputs() or not self.inputs()[self.input]:
            return True  # input is instantly ready

        src_name = self.inputs()[self.input]
        request_text = ConfigGet % (src_name, src_name)
        config = self._request('GET', request_text)

        avail = config.iter('Feature_Availability').next()
        return avail.text == 'Ready'

    def menu_status(self):
        if self.input not in self.inputs() or not self.inputs()[self.input]:
            return True

        src_name = self.inputs()[self.input]
        request_text = ListGet % (src_name, src_name)
        res = self._request(request_text)

        ready = (res.iter("Menu_Status").next().text == "Ready")
        layer = int(res.iter("Menu_Layer").next().text)
        name = res.iter("Menu_Name").next().text
        current_line = int(res.iter("Current_Line").next().text)
        max_line = int(res.iter("Max_Line").next().text)
        current_list = res.iter('Current_List').next()

        cl = {elt.tag: elt.find('Txt').text
              for elt in current_list.getchildren()
              if elt.find('Attribute').text != 'Unselectable'}

        status = MenuStatus(ready, layer, name, current_line, max_line, cl)
        return status

    def menu_jump_line(self, lineno):
        if self.input not in self.inputs() or not self.inputs()[self.input]:
            return None

        src_name = self.inputs()[self.input]
        request_text = ListControlJumpLine % (src_name, lineno, src_name)
        return self._request('PUT', request_text)

    def _menu_cursor(self, action):
        if self.input not in self.inputs() or not self.inputs()[self.input]:
            return None

        src_name = self.inputs()[self.input]
        request_text = ListControlCursor % (src_name, action, src_name)
        return self._request('PUT', request_text)

    def menu_up(self):
        return self._menu_cursor("Up")

    def menu_down(self):
        return self._menu_cursor("Down")

    def menu_sel(self):
        return self._menu_cursor("Sel")

    def menu_return(self):
        return self._menu_cursor("Return")

    @property
    def volume(self):
        request_text = VolumeLevel % 'GetParam'
        response = self._request('GET', request_text)
        vol = response.find('Main_Zone/Volume/Lvl/Val').text
        return float(vol) / 10.0

    @volume.setter
    def volume(self, value):
        value = str(int(value * 10))
        exp = 1
        unit = 'dB'

        request_text = VolumeLevelSet % (value, exp, unit)
        self._request('PUT', request_text)

    def volume_fade(self, final_vol, sleep=0.5):
        start_vol = int(floor(self.volume))
        step = 1 if final_vol > start_vol else -1

        for val in xrange(start_vol, final_vol, step):
            self.volume = val
            time.sleep(sleep)

    def _direct_sel(self, lineno):
        request_text = SelectNetRadioLine % lineno
        return self._request('PUT', request_text)

    @property
    def sleep(self):
        request_text = PowerControlSleep % 'GetParam'
        response = self._request('GET', request_text)
        sleep = response.find("Main_Zone/Power_Control/Sleep").text
        return sleep

    @sleep.setter
    def sleep(self, value):
        request_text = PowerControlSleep % value
        self._request('PUT', request_text)
