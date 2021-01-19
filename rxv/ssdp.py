#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import re
import socket
import xml
from collections import namedtuple

import requests
from defusedxml import cElementTree

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin


SSDP_ADDR = '239.255.255.250'
SSDP_PORT = 1900
SSDP_MSEARCH_QUERY = (
    'M-SEARCH * HTTP/1.1\r\n'
    'MX: 1\r\n'
    'HOST: 239.255.255.250:1900\r\n'
    'MAN: "ssdp:discover"\r\n'
    'ST: upnp:rootdevice\r\n\r\n'
)

URL_BASE_QUERY = '*/{urn:schemas-yamaha-com:device-1-0}X_URLBase'
CONTROL_URL_QUERY = '***/{urn:schemas-yamaha-com:device-1-0}X_controlURL'
UNITDESC_URL_QUERY = '***/{urn:schemas-yamaha-com:device-1-0}X_unitDescURL'
MODEL_NAME_QUERY = (
    "{urn:schemas-upnp-org:device-1-0}device"
    "/{urn:schemas-upnp-org:device-1-0}modelName"
)
FRIENDLY_NAME_QUERY = (
    "{urn:schemas-upnp-org:device-1-0}device"
    "/{urn:schemas-upnp-org:device-1-0}friendlyName"
)
SERIAL_NUMBER_QUERY = (
    "{urn:schemas-upnp-org:device-1-0}device"
    "/{urn:schemas-upnp-org:device-1-0}serialNumber"
)

RxvDetails = namedtuple(
    "RxvDetails",
    "ctrl_url unit_desc_url, model_name friendly_name serial_number"
)


def discover(timeout=1.5):
    """Crude SSDP discovery. Returns a list of RxvDetails objects
       with data about Yamaha Receivers in local network"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    sock.sendto(SSDP_MSEARCH_QUERY.encode("utf-8"), (SSDP_ADDR, SSDP_PORT))
    sock.settimeout(timeout)

    responses = []
    try:
        while True:
            responses.append(sock.recv(10240))
    except socket.timeout:
        pass

    results = []
    for res in responses:
        m = re.search(r"LOCATION:(.+)", res.decode('utf-8'), re.IGNORECASE)
        if not m:
            continue
        url = m.group(1).strip()
        res = rxv_details(url)
        if res:
            results.append(res)

    return results


def rxv_details(location):
    """Looks under given UPNP url, and checks if Yamaha amplituner lives there
       returns RxvDetails if yes, None otherwise"""
    try:
        res = cElementTree.XML(requests.get(location).content)
    except xml.etree.ElementTree.ParseError:
        return None
    url_base_el = res.find(URL_BASE_QUERY)
    if url_base_el is None:
        return None
    ctrl_url_local = res.find(CONTROL_URL_QUERY).text
    ctrl_url = urljoin(url_base_el.text, ctrl_url_local)
    unit_desc_url_local = res.find(UNITDESC_URL_QUERY).text
    unit_desc_url = urljoin(url_base_el.text, unit_desc_url_local)
    model_name = res.find(MODEL_NAME_QUERY).text
    friendly_name = res.find(FRIENDLY_NAME_QUERY).text
    serial_number = res.find(SERIAL_NUMBER_QUERY).text

    return RxvDetails(ctrl_url, unit_desc_url, model_name, friendly_name, serial_number)


if __name__ == '__main__':
    print(discover())
