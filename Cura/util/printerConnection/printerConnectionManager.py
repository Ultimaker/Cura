__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

from Cura.util import version
from Cura.util.printerConnection import dummyConnection
from Cura.util.printerConnection import doodle3dConnect

class connectionEntry(object):
	def __init__(self, name, priority, icon, connection):
		self.name = name
		self.priority = priority
		self.icon = icon
		self.connection = connection
		self.window = None

	def __cmp__(self, other):
		return self.priority - other.priority

	def __repr__(self):
		return self.name

class PrinterConnectionManager(object):
	def __init__(self):
		self._connectionList = []
		if version.isDevVersion():
			self._connectionList.append(connectionEntry('Dummy', -1, 5, dummyConnection.dummyConnection()))
		self._connectionList.append(connectionEntry('Doodle3D', 100, 27, doodle3dConnect.doodle3dConnect()))

		#Sort the connections by highest priority first.
		self._connectionList.sort(reverse=True)

	#Return the highest priority available connection.
	def getAvailableConnection(self):
		for e in self._connectionList:
			if e.connection.isAvailable():
				return e
		return None
