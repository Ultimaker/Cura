"""
The printer connection manager keeps track of all the possible printer connections that can be made.
It sorts them by priority and gives easy access to the first available connection type.

This is used by the print/save button to give access to the first available print connection.
As well as listing all printers under the right mouse button.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

from Cura.util import profile
from Cura.util import version
from Cura.util.printerConnection import dummyConnection
from Cura.util.printerConnection import serialConnection
from Cura.util.printerConnection import doodle3dConnect

class PrinterConnectionManager(object):
	"""
	The printer connection manager has one of each printer connection groups. Sorted on priority.
	It can retrieve the first available connection as well as all available connections.
	"""
	def __init__(self):
		self._groupList = []
		if version.isDevVersion():
			self._groupList.append(dummyConnection.dummyConnectionGroup())
		self._groupList.append(serialConnection.serialConnectionGroup())
		self._groupList.append(doodle3dConnect.doodle3dConnectionGroup())

		#Sort the connections by highest priority first.
		self._groupList.sort(reverse=True)

	#Return the highest priority available connection.
	def getAvailableGroup(self):
		if profile.getMachineSetting('gcode_flavor') == 'UltiGCode':
			return None
		for g in self._groupList:
			if len(g.getAvailableConnections()) > 0:
				return g
		return None

	#Return all available connections.
	def getAvailableConnections(self):
		ret = []
		for e in self._groupList:
			ret += e.getAvailableConnections()
		return ret
