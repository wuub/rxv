rxv
===

Automation Library for Yamaha RX-V473, RX-V573, RX-V673, RX-V773 receivers

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
* `@Raynes <https:/github.com/Raynes>`_
* `@sdague <https://github.com/sdague>`_

Users
=====

* `rxvc <https://github.com/Raynes/rxvc>`_
