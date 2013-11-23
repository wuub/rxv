#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division, absolute_import, print_function


class RXVException(Exception):
    pass


class ReponseException(RXVException):
    """Exception raised when yamaha receiver responded with an error code"""
    pass

class MenuUnavailable(RXVException):
    """Menu control unavailable for current input"""
    pass
