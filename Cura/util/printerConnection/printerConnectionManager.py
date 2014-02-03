__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

from Cura.util import profile
from Cura.util import version
from Cura.util.printerConnection import dummyConnection
from Cura.util.printerConnection import serialConnection
from Cura.util.printerConnection import doodle3dConnect

class PrinterConnectionManager(object):
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
