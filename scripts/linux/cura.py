#!/usr/bin/python

import os, sys

try:
    import OpenGL
    import wx
    import serial
    import numpy
    import power
except ImportError as e:
    module = e.message.lstrip('No module named ')
    print 'Requires ' + module

    if module == 'power':
        print "Install from: https://github.com/GreatFruitOmsk/Power"
    else:
        print "Try sudo easy_install " + module

sys.path.insert(1, os.path.dirname(__file__))

import Cura.cura as cura

cura.main()
