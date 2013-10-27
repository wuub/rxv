#!/usr/bin/env python
from rxv import RXV473
from pprint import pprint


def main():
    rx = RXV473('10.0.0.55')
    rx.on = True
    pprint(rx.basic_status)
    pprint(rx.inputs())

    rx.input = 'HDMI3'
    rx.volume = -50
    rx.volume_fade(-50)


if __name__ == '__main__':
    main()
