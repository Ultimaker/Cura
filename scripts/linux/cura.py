#!/usr/bin/python

import os, sys

sys.path.insert(1, os.path.dirname(__file__))

try:
	import OpenGL
	import wx
	import serial
	import numpy
	import power
except ImportError as e:
	if e.message[0:16] == 'No module named ':
		module = e.message[16:]

		if module == 'OpenGL':
			module = 'PyOpenGL'
		elif module == 'serial':
			module = 'pyserial'
		print 'Requires ' + module

		if module == 'power':
			print "Install from: https://github.com/GreatFruitOmsk/Power"
		else:
			print "Try sudo easy_install " + module
		print e.message
    
	exit(1)


import Cura.cura as cura

cura.main()
