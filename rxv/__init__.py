#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

import logging

from . import ssdp
from .rxv import RXV

__all__ = ['RXV']

# disable default logging of warnings to stderr. If a consuming
# application sets up logging, it will work as expected.
logging.getLogger('rxv').addHandler(logging.NullHandler())


def find(timeout=1.5):
    """Find all Yamah receivers on local network using SSDP search."""
    return [RXV(**ri._asdict()) for ri in ssdp.discover(timeout=timeout)]
