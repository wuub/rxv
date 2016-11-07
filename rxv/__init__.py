#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function
import logging

from .rxv import RXV
from .rxv import PlaybackSupport
from . import ssdp

__all__ = ['RXV']

# disable default logging of warnings to stderr. If a consuming
# application sets up logging, it will work as expected.
logging.getLogger('rxv').addHandler(logging.NullHandler())


def find(timeout=1.5):
    """Find all Yamah receivers on local network using SSDP search."""
    return [
        RXV(
            ctrl_url=ri.ctrl_url,
            model_name=ri.model_name,
            friendly_name=ri.friendly_name,
            unit_desc_url=ri.unit_desc_url
        )
        for ri in ssdp.discover(timeout=timeout)
    ]
