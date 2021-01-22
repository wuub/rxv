#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function


class RXVException(Exception):
    pass


class ResponseException(RXVException):
    """Exception raised when yamaha receiver responded with an error code"""
    pass


ReponseException = ResponseException


class MenuUnavailable(RXVException):
    """Menu control unavailable for current input"""
    pass


class MenuActionUnavailable(RXVException):
    """Menu control action unavailable for current input"""
    def __init__(self, input, action):
        super().__init__(f'{input} does not support menu cursor {action}')


class PlaybackUnavailable(RXVException):
    """Raised when playback function called on unsupported source."""
    def __init__(self, source, action):
        super().__init__('{} does not support {}'.format(source, action))


class CommandUnavailable(RXVException):
    """Raised when command is called on unsupported device."""
    def __init__(self, zone, command):
        super().__init__('{} does not support {}'.format(zone, command))


class UnknownPort(RXVException):
    """Raised when an unknown port is found."""
    def __init__(self, port):
        super().__init__('port {} is not supported'.format(port))
