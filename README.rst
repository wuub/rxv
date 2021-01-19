rxv 
===
.. image:: https://badge.fury.io/py/rxv.svg
    :target: https://badge.fury.io/py/rxv


Automation Library for Yamaha receivers

Installation
============

Use pip::

  $ pip install rxv
  or
  $ pip install --use-wheel rxv


Usage
=====

The easiest way to start using is to let SSDP find all available receivers.
In most cases **rxv** module will manage to obtain locations of local compatible devices::

  >>> import rxv
  >>> receivers = rxv.find()
  >>> print(receivers)
  [<RXV model_name="RX-V473" ctrl_url="http://192.168.1.116:80/YamahaRemoteControl/ctrl" at 0x2c1c1d0>]
  >>> rx = receivers[0]
  >>> rx.on = True
  >>> rx.volume
  -51.0
  >>> rx.inputs()
  {'AUDIO': None,
  'HDMI1': None,
  'HDMI2': None,
  (...)
  'iPod (USB)': 'iPod_USB'}
  >>> rx.input
  "NET RADIO"
  >>> rx.input = "HDMI1"
  >>> rx.input
  "HDMI1"
  >>> rx.is_playback_supported()
  False
  >>> rx.input = "AirPlay"
  >>> rx.is_playback_supported()
  True
  >>> from rxv import PlaybackSupport
  >>> (rx.get_playback_support() & PlaybackSupport.PLAY) != 0
  True
  >>> rx.play()
  >>> rx.next()
  >>> rx.outputs
  {'hdmi2': 'off', 'hdmi1': 'on'}
  >>> rx.enable_output('hdmi2', True)
  >>> rx.enable_output('hdmi1', False)
  >>> rx.outputs
  {'hdmi2': 'on', 'hdmi1': 'off'}


If SSDP causes you some problems, `ctrl_url` can be provided by hand.::

  >>> rx = rxv.RXV("http://192.168.1.116:80/YamahaRemoteControl/ctrl", "RX-V473")


License
=======

BSD


Authors
=======

* `@jnnt <https://github.com/jnnt>`_
* `@wuub <https://github.com/wuub>`_

Contributors
============

* `@briancline <https://github.com/briancline>`_
* `@rthill <https://github.com/rthill>`_
* `@jtai <https://github.com/jtai>`_
* `@ahocquet <https://github.com/ahocquet>`_
* `@Raynes <https://github.com/Raynes>`_
* `@sdague <https://github.com/sdague>`_
* `@postlund <https://github.com/postlund>`_
* `@HerrHofrat <https://github.com/HerrHofrat>`_
* `@mischuh <https://github.com/mischuh>`_


Users
=====

* `Home Assistant <https://github.com/home-assistant/home-assistant/>`_
* `rxvc <https://github.com/Raynes/rxvc>`_
