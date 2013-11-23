#!/usr/bin/env python
import rxv
import time
from pprint import pprint

def main():
    rx = rxv.find()[0]
    rx.on = True

    time.sleep(1.0)
    pprint(rx.basic_status)
    pprint(rx.inputs())

    rx.input = 'HDMI3'
    rx.volume = -50
    rx.volume_fade(-40)
    rx.volume_fade(-45)


if __name__ == '__main__':
    main()
