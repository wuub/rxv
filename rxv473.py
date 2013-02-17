#! /usr/bin/env python

import requests
import xml.etree.ElementTree as ET
from collections import namedtuple

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900

BasicStatus = namedtuple("BasicStatus", "on volume mute input")
MenuStatus = namedtuple("MenuStatus", "ready layer name current_line max_line current_list")


class RXV473(object):

    def __init__(self, ip):
        self._ip = ip
        self._inputs_cache = None

    @property
    def ctrl_url(self):
        return 'http://192.168.1.116:80/YamahaRemoteControl/ctrl'

    def _request(self, request_text):
        res = requests.post(self.ctrl_url, data=request_text, headers={"Content-Type": "text/xml"})
        response = ET.XML(res.content)
        assert response.get("RC") == "0"
        return response

    @property
    def basic_status(self):
        request_text = '<YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>'
        response = self._request(request_text)
        on = response.find("Main_Zone/Basic_Status/Power_Control/Power").text
        volume = int(response.find("Main_Zone/Basic_Status/Volume/Lvl/Val").text) / 10.0
        mute = response.find("Main_Zone/Basic_Status/Volume/Mute").text
        inp = response.find("Main_Zone/Basic_Status/Input/Input_Sel").text

        bs = BasicStatus(on, volume, mute, inp)
        return bs

    @property
    def on(self):
        request_text = '<YAMAHA_AV cmd="GET"><Main_Zone><Power_Control><Power>GetParam</Power></Power_Control></Main_Zone></YAMAHA_AV>'
        response = self._request(request_text)
        power = response.find("Main_Zone/Power_Control/Power").text
        assert power in ["On", "Standby"]
        return power == "On"

    @on.setter
    def on(self, value):
        assert value in [True, False]
        new_value = "On" if value else "Standby"
        template = '<YAMAHA_AV cmd="PUT"><Main_Zone><Power_Control><Power>{value}</Power></Power_Control></Main_Zone></YAMAHA_AV>'
        request_text = template.format(value=new_value)
        response = self._request(request_text)
        return response

    @property
    def input(self):
        request_text = '<YAMAHA_AV cmd="GET"><Main_Zone><Input><Input_Sel>GetParam</Input_Sel></Input></Main_Zone></YAMAHA_AV>'
        response = self._request(request_text)
        return response.find("Main_Zone/Input/Input_Sel").text

    @input.setter
    def input(self, input_name):
        assert input_name in self.inputs()
        template = '<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>{input_name}</Input_Sel></Input></Main_Zone></YAMAHA_AV>'
        request_text = template.format(input_name=input_name)
        self._request(request_text)

    def inputs(self):
        if not self._inputs_cache:
            res = self._request('<YAMAHA_AV cmd="GET"><Main_Zone><Input><Input_Sel_Item>GetParam</Input_Sel_Item></Input></Main_Zone></YAMAHA_AV>')
            self._inputs_cache = dict(zip((elt.text for elt in res.iter('Param')), (elt.text for elt in res.iter("Src_Name"))))
        return self._inputs_cache

    def is_ready(self):

        src_name = self.inputs()[self.input]
        if not src_name:
            return True  # no SrcName -> input is instantly ready
        template = '<YAMAHA_AV cmd="GET"><{src_name}><Config>GetParam</Config></{src_name}></YAMAHA_AV>'
        config = self._request(template.format(src_name=src_name))
        avail = config.iter('Feature_Availability').next()
        return avail.text == 'Ready'

    def menu_status(self):
        template = '<YAMAHA_AV cmd="GET"><{src_name}><List_Info>GetParam</List_Info></{src_name}></YAMAHA_AV>'
        src_name = self.inputs()[self.input]
        if not src_name:
            return None

        res = self._request(template.format(src_name=src_name))
        ready = res.iter("Menu_Status").next().text == "Ready"
        layer = int(res.iter("Menu_Layer").next().text)
        name = res.iter("Menu_Name").next().text
        current_line = int(res.iter("Current_Line").next().text)
        max_line = int(res.iter("Max_Line").next().text)
        current_list = res.iter('Current_List').next()

        cl = {elt.tag: elt.find('Txt').text for elt in current_list.getchildren() if elt.find('Attribute').text != 'Unselectable'}

        ms = MenuStatus(ready, layer, name, current_line, max_line, cl)
        return ms

    def menu_jump_line(self, lineno):
        src_name = self.inputs()[self.input]
        if not src_name:
            return None
        template = '<YAMAHA_AV cmd="PUT"><{src_name}><List_Control><Jump_Line>{lineno}</Jump_Line></List_Control></{src_name}></YAMAHA_AV>'
        return self._request(template.format(lineno=lineno, src_name=src_name))

    def _menu_cursor(self, action):
        src_name = self.inputs()[self.input]
        if not src_name:
            return None
        template = '<YAMAHA_AV cmd="PUT"><{src_name}><List_Control><Cursor>{action}</Cursor></List_Control></{src_name}></YAMAHA_AV>'
        request_text = template.format(src_name=src_name, action=action)
        return self._request(request_text)

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
        request_text = '<YAMAHA_AV cmd="GET"><Main_Zone><Volume><Lvl>GetParam</Lvl></Volume></Main_Zone></YAMAHA_AV>'
        response = self._request(request_text)
        vol = response.find('Main_Zone/Volume/Lvl/Val')
        return float(vol.text) / 10.0

    @volume.setter
    def volume(self, value):
        val = str(int(value * 10))  # '{:.1f}'.format(value * 10.0)
        template = '<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Lvl><Val>{value}</Val><Exp>1</Exp><Unit>dB</Unit></Lvl></Volume></Main_Zone></YAMAHA_AV>'
        request_text = template.format(value=val)
        self._request(request_text)

    def _direct_sel(self, lineno):
        template = '<YAMAHA_AV cmd="PUT"><NET_RADIO><List_Control><Direct_Sel>Line_{num}</Direct_Sel></List_Control></NET_RADIO></YAMAHA_AV>'
        request_text = template.format(num=lineno)
        return self._request(request_text)

    @property
    def sleep(self):
        request_text = '<YAMAHA_AV cmd="GET"><Main_Zone><Power_Control><Sleep>GetParam</Sleep></Power_Control></Main_Zone></YAMAHA_AV>'
        response = self._request(request_text)
        sleep = response.find("Main_Zone/Power_Control/Sleep").text
        return sleep

    @sleep.setter
    def sleep(self, value):
        template = '<YAMAHA_AV cmd="PUT"><Main_Zone><Power_Control><Sleep>{value}</Sleep></Power_Control></Main_Zone></YAMAHA_AV>'
        request_text = template.format(value=value)
        self._request(request_text)


def main():
    import time
    rx = RXV473("")
    rx.on = True
    time.sleep(5)
    rx.volume = -80.0
    rx.sleep = "90 min"

    rx.input = 'NET RADIO'

    time.sleep(10)
    while not rx.is_ready():
        time.sleep(0.5)

    while not rx.menu_status().ready:
        time.sleep(0.5)

    time.sleep(10)
    rx._direct_sel(1)

    time.sleep(10)
    rx._direct_sel(2)
    time.sleep(10)

    for val in range(-80, -55, 1):
        rx.volume = val
        time.sleep(0.5)

if __name__ == '__main__':
    main()
