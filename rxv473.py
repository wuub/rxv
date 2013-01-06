#! /usr/bin/env python

import requests
import xml.etree.ElementTree as ET

SSDP_ADDR = "239.255.255.250"
SSDP_PORT = 1900


class RXV473(object):

    def __init__(self, ip):
        self._ip = ip

    @property
    def ctrl_url(self):
        return 'http://192.168.1.116:80/YamahaRemoteControl/ctrl'

    def _request(self, request_text):
        res = requests.post(self.ctrl_url, data=request_text, headers={"Content-Type": "text/xml"})
        response = ET.XML(res.content)
        assert response.get("RC") == "0"
        return response

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
        input = response.find("Main_Zone/Input/Input_Sel").text
        return input

    @input.setter
    def input(self, input_name):
        assert input_name in self.inputs()
        template = '<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>{input_name}</Input_Sel></Input></Main_Zone></YAMAHA_AV>'
        request_text = template.format(input_name=input_name)
        response = self._request(request_text)
        return response

    def inputs(self):
        res = self._request('<YAMAHA_AV cmd="GET"><Main_Zone><Input><Input_Sel_Item>GetParam</Input_Sel_Item></Input></Main_Zone></YAMAHA_AV>')
        return [elt.text for elt in res.iter('Param')]

    @property
    def volume(self):
        request_text = '<YAMAHA_AV cmd="GET"><Main_Zone><Volume><Lvl>GetParam</Lvl></Volume></Main_Zone></YAMAHA_AV>'
        response = self._request(request_text)
        vol = response.find('Main_Zone/Volume/Lvl/Val')
        return float(vol.text) / 10.0

    @volume.setter
    def volume(self, value):

        val = str(int(value * 10))  # '{:.1f}'.format(value * 10.0)
        print val
        template = '<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Lvl><Val>{value}</Val><Exp>1</Exp><Unit>dB</Unit></Lvl></Volume></Main_Zone></YAMAHA_AV>'
        request_text = template.format(value=val)
        response = self._request(request_text)
        return response

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
        response = self._request(request_text)
        return response


def main():
    import time
    rx = RXV473("")

    rx.on = True
    while not rx.on:
        time.sleep(0.5)

    rx.input = 'NET RADIO'

    time.sleep(5)
    rx.volume = -80.0
    rx.sleep = "90 min"
    time.sleep(30)
    rx._direct_sel(1)
    time.sleep(30)
    rx._direct_sel(4)

    for val in range(-80, -44, 1):
        rx.volume = val
        time.sleep(0.5)
    """
    rx.on = True
    rx.on = False
    """

    """
    rx.volume = -41.2
    rx.volume

    <YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>SERVER</Input_Sel></Input></Main_Zone></YAMAHA_AV>
    Tuner, AirPlay, iPod_USB, USB, NET_RADIO, SERVER, HDMI1, HDMI2, HDMI3, HDMI4
   ['NET RADIO', 'SERVER', 'AirPlay', 'USB', 'iPod (USB)', 'TUNER', 'HDMI1', 'HDMI2',
   'HDMI3', 'HDMI4', 'AV1', 'AV2', 'AV3', 'AV4', 'AV5', 'AV6', 'AUDIO', 'V-AUX']
    rx.input = "usb"

    rx.play()
    rx.pause()
    rx.stop()

    rx.skip_fwd()
    rx.skip_rev()

    <YAMAHA_AV cmd="GET"><Main_Zone><Basic_Status>GetParam</Basic_Status></Main_Zone></YAMAHA_AV>HTTP/1.1 200 OK

<YAMAHA_AV rsp="GET" RC="0"><Main_Zone><Basic_Status><Power_Control><Power>On</Power><Sleep>Off</Sleep></Power_Control><Volume><Lvl><Val>-455</Val><Exp>1</Exp><Unit>dB</Unit></Lvl><Mute>Off</Mute></Volume><Input><Input_Sel>SERVER</Input_Sel><Input_Sel_Item_Info><Param>SERVER</Param><RW>RW</RW><Title> SERVER  </Title><Icon><On>/YamahaRemoteControl/Icons/icon006.png</On><Off></Off></Icon><Src_Name>SERVER</Src_Name><Src_Number>1</Src_Number></Input_Sel_Item_Info></Input><Surround><Program_Sel><Current><Straight>Off</Straight><Enhancer>On</Enhancer><Sound_Program>2ch Stereo</Sound_Program></Current></Program_Sel><_3D_Cinema_DSP>Off</_3D_Cinema_DSP></Surround><Sound_Video><Tone><Bass><Val>0</Val><Exp>1</Exp><Unit>dB</Unit></Bass><Treble><Val>0</Val><Exp>1</Exp><Unit>dB</Unit></Treble></Tone><Direct><Mode>Off</Mode></Direct><HDMI><Standby_Through_Info>On</Standby_Through_Info><Output><OUT_1>On</OUT_1></Output></HDMI><Adaptive_DRC>Auto</Adaptive_DRC></Sound_Video></Basic_Status></Main_Zone></YAMAHA_AV>

*********************************************
<?xml version="1.0" encoding="utf-8"?><YAMAHA_AV cmd="GET"><NET_RADIO><Config>GetParam</Config></NET_RADIO></YAMAHA_AV>HTTP/1.1 200 OK

Server: AV_Receiver/3.1 (RX-V473)

Content-Type: text/xml; charset="utf-8"

Content-Length: 130



<YAMAHA_AV rsp="GET" RC="0"><NET_RADIO><Config><Feature_Availability>Ready</Feature_Availability></Config></NET_RADIO></YAMAHA_AV>

******************************************
<?xml version="1.0" encoding="utf-8"?><YAMAHA_AV cmd="GET"><NET_RADIO><List_Info>GetParam</List_Info></NET_RADIO></YAMAHA_AV>HTTP/1.1 200 OK

Server: AV_Receiver/3.1 (RX-V473)

Content-Type: text/xml; charset="utf-8"

Content-Length: 839



<YAMAHA_AV rsp="GET" RC="0"><NET_RADIO><List_Info><Menu_Status>Ready</Menu_Status><Menu_Layer>1</Menu_Layer><Menu_Name>NET RADIO</Menu_Name><Current_List><Line_1><Txt>Bookmarks</Txt><Attribute>Container</Attribute></Line_1><Line_2><Txt>Locations</Txt><Attribute>Container</Attribute></Line_2><Line_3><Txt>Genres</Txt><Attribute>Container</Attribute></Line_3><Line_4><Txt>New Stations</Txt><Attribute>Container</Attribute></Line_4><Line_5><Txt>Popular Stations</Txt><Attribute>Container</Attribute></Line_5><Line_6><Txt>Podcasts</Txt><Attribute>Container</Attribute></Line_6><Line_7><Txt>Help</Txt><Attribute>Container</Attribute></Line_7><Line_8><Txt></Txt><Attribute>Unselectable</Attribute></Line_8></Current_List><Cursor_Position><Current_Line>1</Current_Line><Max_Line>7</Max_Line></Cursor_Position></List_Info></NET_RADIO></YAMAHA_AV>
    """

if __name__ == '__main__':
    main()
