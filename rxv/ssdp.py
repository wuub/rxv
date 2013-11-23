#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function

import io
import socket
import requests
import mimetools
from urlparse import urljoin
from collections import namedtuple
import xml.etree.ElementTree as ET

SSDP_ADDR = '239.255.255.250'
SSDP_PORT = 1900
SSDP_MSEARCH_QUERY = \
   'M-SEARCH * HTTP/1.1\r\n' \
   'MX: 1\r\n' \
   'HOST: 239.255.255.250:1900\r\n' \
   'MAN: "ssdp:discover"\r\n' \
   'ST: upnp:rootdevice\r\n\r\n'

URL_BASE_QUERY = '*/{urn:schemas-yamaha-com:device-1-0}X_URLBase'
CONTROL_URL_QUERY = '***/{urn:schemas-yamaha-com:device-1-0}X_controlURL'
MODEL_NAME_QUERY = "{urn:schemas-upnp-org:device-1-0}device/{urn:schemas-upnp-org:device-1-0}modelName"


RxvDetails = namedtuple("RxvDetails", "model_name control_url")


def discover():
    """Crude SSDP discovery. Returns a list of RxvDetails objects
       with data about Yamaha Receivers in local network"""
    socket.setdefaulttimeout(1.0)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(SSDP_MSEARCH_QUERY, (SSDP_ADDR, SSDP_PORT))

    responses = []
    try:
        while True:
            responses.append(sock.recv(10240))
    except socket.timeout:
        pass

    results = []
    for res in responses:
        _, headers = res.split('\r\n', 1)
        msg = mimetools.Message(io.StringIO(headers.decode("utf-8")))
        res = rxv_details(msg['LOCATION'])
        if res:
            results.append(res)

    return results


def rxv_details(location):
    """Looks under given UPNP url, and checks if Yamaha amplituner lives there
       returns RxvDetails if yes, None otherwise"""
    xml = ET.XML(requests.get(location).content)
    url_base_el = xml.find(URL_BASE_QUERY)
    if url_base_el is None:
        return None
    control_url = xml.find(CONTROL_URL_QUERY).text
    model_name = xml.find(MODEL_NAME_QUERY).text
    control_url = urljoin(url_base_el.text, control_url)

    return RxvDetails(model_name, control_url)


if __name__ == '__main__':
    print(discover())
