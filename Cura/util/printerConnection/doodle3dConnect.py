"""
Doodle3D printer connection. Auto-detects any Doodle3D boxes on the local network, and finds if they have a printer connected.
This connection can then be used to send GCode to the printer.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import threading
import json
import httplib as httpclient
import urllib
import time

from Cura.util.printerConnection import printerConnectionBase

class doodle3dConnectionGroup(printerConnectionBase.printerConnectionGroup):
	"""
	The Doodle3D connection group runs a thread to poll for Doodle3D boxes.
	For each Doodle3D box it finds, it creates a Doodle3DConnect object.
	"""
	PRINTER_LIST_HOST = 'connect.doodle3d.com'
	PRINTER_LIST_PATH = '/api/list.php'

	def __init__(self):
		super(doodle3dConnectionGroup, self).__init__("Doodle3D")
		self._http = None
		self._host = self.PRINTER_LIST_HOST
		self._connectionMap = {}

		self._thread = threading.Thread(target=self._doodle3DThread)
		self._thread.daemon = True
		self._thread.start()

	def getAvailableConnections(self):
		return filter(lambda c: c.isAvailable(), self._connectionMap.values())

	def remove(self, host):
		del self._connectionMap[host]

	def getIconID(self):
		return 27

	def getPriority(self):
		return 100

	def _doodle3DThread(self):
		self._waitDelay = 0
		while True:
			printerList = self._request('GET', self.PRINTER_LIST_PATH)
			if not printerList or type(printerList) is not dict or 'data' not in printerList or type(printerList['data']) is not list:
				#Check if we are connected to the Doodle3D box in access point mode, as this gives an
				# invalid reply on the printer list API
				printerList = {'data': [{'localip': 'draw.doodle3d.com'}]}

			#Add the 192.168.5.1 IP to the list of printers to check, as this is the LAN port IP, which could also be available.
			# (connect.doodle3d.com also checks for this IP in the javascript code)
			printerList['data'].append({'localip': '192.168.5.1'})

			#Check the status of each possible IP, if we find a valid box with a printer connected. Use that IP.
			for possiblePrinter in printerList['data']:
				if possiblePrinter['localip'] not in self._connectionMap:
					status = self._request('GET', '/d3dapi/config/?network.cl.wifiboxid=', host=possiblePrinter['localip'])
					if status and 'data' in status and 'network.cl.wifiboxid' in status['data']:
						name = status['data']['network.cl.wifiboxid']
						if 'wifiboxid' in possiblePrinter:
							name = possiblePrinter['wifiboxid']
						self._connectionMap[possiblePrinter['localip']] = doodle3dConnect(possiblePrinter['localip'], name, self)

			# Delay a bit more after every request. This so we do not stress the connect.doodle3d.com api too much
			if self._waitDelay < 10:
				self._waitDelay += 1
			time.sleep(self._waitDelay * 60)

	def _request(self, method, path, postData = None, host = None):
		if host is None:
			host = self._host
		if self._http is None or self._http.host != host:
			self._http = httpclient.HTTPConnection(host, timeout=30)

		try:
			if postData is not None:
				self._http.request(method, path, urllib.urlencode(postData), {"Content-type": "application/x-www-form-urlencoded", "User-Agent": "Cura Doodle3D connection"})
			else:
				self._http.request(method, path, headers={"Content-type": "application/x-www-form-urlencoded", "User-Agent": "Cura Doodle3D connection"})
		except:
			self._http.close()
			return None
		try:
			response = self._http.getresponse()
			responseText = response.read()
		except:
			self._http.close()
			return None
		try:
			response = json.loads(responseText)
		except ValueError:
			self._http.close()
			return None
		if response['status'] != 'success':
			return False

		return response

class doodle3dConnect(printerConnectionBase.printerConnectionBase):
	"""
	Class to connect and print files with the doodle3d.com wifi box
	Auto-detects if the Doodle3D box is available with a printer and handles communication with the Doodle3D API
	"""
	def __init__(self, host, name, group):
		super(doodle3dConnect, self).__init__(name)

		self._http = None
		self._group = group
		self._host = host

		self._isAvailable = False
		self._printing = False
		self._fileBlocks = []
		self._commandList = []
		self._blockIndex = None
		self._lineCount = 0
		self._progressLine = 0
		self._hotendTemperature = [None] * 4
		self._bedTemperature = None
		self._errorCount = 0
		self._interruptSleep = False

		self.checkThread = threading.Thread(target=self._doodle3DThread)
		self.checkThread.daemon = True
		self.checkThread.start()

	#Load the file into memory for printing.
	def loadGCodeData(self, dataStream):
		if self._printing:
			return False
		self._fileBlocks = []
		self._lineCount = 0
		block = []
		blockSize = 0
		for line in dataStream:
			#Strip out comments, we do not need to send comments
			if ';' in line:
				line = line[:line.index(';')]
			#Strip out whitespace at the beginning/end this saves data to send.
			line = line.strip()

			if len(line) < 1:
				continue
			self._lineCount += 1
			#Put the lines in 8k sized blocks, so we can send those blocks as http requests.
			if blockSize + len(line) > 1024 * 8:
				self._fileBlocks.append('\n'.join(block) + '\n')
				block = []
				blockSize = 0
			blockSize += len(line) + 1
			block.append(line)
		self._fileBlocks.append('\n'.join(block) + '\n')
		self._doCallback()
		return True

	#Start printing the previously loaded file
	def startPrint(self):
		if self._printing or len(self._fileBlocks) < 1:
			return
		self._progressLine = 0
		self._blockIndex = 0
		self._printing = True
		self._interruptSleep = True

	#Abort the previously loaded print file
	def cancelPrint(self):
		if not self._printing:
			return
		if self._request('POST', '/d3dapi/printer/stop', {'gcode': 'M104 S0\nG28'}):
			self._printing = False

	def isPrinting(self):
		return self._printing

	#Amount of progression of the current print file. 0.0 to 1.0
	def getPrintProgress(self):
		if self._lineCount < 1:
			return 0.0
		return float(self._progressLine) / float(self._lineCount)

	# Return if the printer with this connection type is available
	def isAvailable(self):
		return self._isAvailable

	#Are we able to send a direct coammand with sendCommand at this moment in time.
	def isAbleToSendDirectCommand(self):
		#The delay on direct commands is very high and so we disabled it.
		return False #self._isAvailable and not self._printing

	#Directly send a command to the printer.
	def sendCommand(self, command):
		if not self._isAvailable or self._printing:
			return
		self._commandList.append(command)
		self._interruptSleep = True

	# Get the connection status string. This is displayed to the user and can be used to communicate
	#  various information to the user.
	def getStatusString(self):
		if not self._isAvailable:
			return "Doodle3D box not found"
		if self._printing:
			if self._blockIndex < len(self._fileBlocks):
				ret = "Sending GCode: %.1f%%" % (float(self._blockIndex) * 100.0 / float(len(self._fileBlocks)))
			elif len(self._fileBlocks) > 0:
				ret = "Finished sending GCode to Doodle3D box."
			else:
				ret = "Different print still running..."
			#ret += "\nErrorCount: %d" % (self._errorCount)
			return ret
		return "Printer found, waiting for print command."

	#Get the temperature of an extruder, returns None is no temperature is known for this extruder
	def getTemperature(self, extruder):
		return self._hotendTemperature[extruder]

	#Get the temperature of the heated bed, returns None is no temperature is known for the heated bed
	def getBedTemperature(self):
		return self._bedTemperature

	def _doodle3DThread(self):
		while True:
			stateReply = self._request('GET', '/d3dapi/info/status')
			if stateReply is None or not stateReply:
				# No API, wait 5 seconds before looking for Doodle3D again.
				# API gave back an error (this can happen if the Doodle3D box is connecting to the printer)
				# The Doodle3D box could also be offline, if we reach a high enough errorCount then assume the box is gone.
				self._errorCount += 1
				if self._errorCount > 10:
					if self._isAvailable:
						self._printing = False
						self._isAvailable = False
						self._doCallback()
					self._sleep(15)
					self._group.remove(self._host)
					return
				else:
					self._sleep(3)
				continue
			if stateReply['data']['state'] == 'disconnected':
				# No printer connected, we do not have a printer available, but the Doodle3D box is there.
				# So keep trying to find a printer connected to it.
				if self._isAvailable:
					self._printing = False
					self._isAvailable = False
					self._doCallback()
				self._sleep(15)
				continue
			self._errorCount = 0

			#We got a valid status, set the doodle3d printer as available.
			if not self._isAvailable:
				self._isAvailable = True

			if 'hotend' in stateReply['data']:
				self._hotendTemperature[0] = stateReply['data']['hotend']
			if 'bed' in stateReply['data']:
				self._bedTemperature = stateReply['data']['bed']

			if stateReply['data']['state'] == 'idle' or stateReply['data']['state'] == 'buffering':
				if self._printing:
					if self._blockIndex < len(self._fileBlocks):
						if self._request('POST', '/d3dapi/printer/print', {'gcode': self._fileBlocks[self._blockIndex], 'start': 'True', 'first': 'True'}):
							self._blockIndex += 1
						else:
							self._sleep(1)
					else:
						self._printing = False
				else:
					if len(self._commandList) > 0:
						if self._request('POST', '/d3dapi/printer/print', {'gcode': self._commandList[0], 'start': 'True', 'first': 'True'}):
							self._commandList.pop(0)
						else:
							self._sleep(1)
					else:
						self._sleep(5)
			elif stateReply['data']['state'] == 'printing':
				if self._printing:
					if self._blockIndex < len(self._fileBlocks):
						for n in xrange(0, 5):
							if self._blockIndex < len(self._fileBlocks):
								if self._request('POST', '/d3dapi/printer/print', {'gcode': self._fileBlocks[self._blockIndex]}):
									self._blockIndex += 1
								else:
									#Cannot send new block, wait a bit, so we do not overload the API
									self._sleep(15)
									break
					else:
						#If we are no longer sending new GCode delay a bit so we request the status less often.
						self._sleep(5)
					if 'current_line' in stateReply['data']:
						self._progressLine = stateReply['data']['current_line']
				else:
					#Got a printing state without us having send the print file, set the state to printing, but make sure we never send anything.
					if 'current_line' in stateReply['data'] and 'total_lines' in stateReply['data'] and stateReply['data']['total_lines'] > 2:
						self._printing = True
						self._fileBlocks = []
						self._blockIndex = 1
						self._progressLine = stateReply['data']['current_line']
						self._lineCount = stateReply['data']['total_lines']
					self._sleep(5)
			self._doCallback()

	def _sleep(self, timeOut):
		while timeOut > 0.0:
			if not self._interruptSleep:
				time.sleep(0.1)
			timeOut -= 0.1
		self._interruptSleep = False

	def _request(self, method, path, postData = None, host = None):
		if host is None:
			host = self._host
		if self._http is None or self._http.host != host:
			self._http = httpclient.HTTPConnection(host, timeout=30)

		try:
			if postData is not None:
				self._http.request(method, path, urllib.urlencode(postData), {"Content-type": "application/x-www-form-urlencoded", "User-Agent": "Cura Doodle3D connection"})
			else:
				self._http.request(method, path, headers={"Content-type": "application/x-www-form-urlencoded", "User-Agent": "Cura Doodle3D connection"})
		except:
			self._http.close()
			return None
		try:
			response = self._http.getresponse()
			responseText = response.read()
		except:
			self._http.close()
			return None
		try:
			response = json.loads(responseText)
		except ValueError:
			self._http.close()
			return None
		if response['status'] != 'success':
			return False

		return response

if __name__ == '__main__':
	d = doodle3dConnect()
	print 'Searching for Doodle3D box'
	while not d.isAvailable():
		time.sleep(1)

	while d.isPrinting():
		print 'Doodle3D already printing! Requesting stop!'
		d.cancelPrint()
		time.sleep(5)

	print 'Doodle3D box found, printing!'
	d.loadFile("C:/Models/belt-tensioner-wave_export.gcode")
	d.startPrint()
	while d.isPrinting() and d.isAvailable():
		time.sleep(1)
		print d.getTemperature(0), d.getStatusString(), d.getPrintProgress(), d._progressLine, d._lineCount, d._blockIndex, len(d._fileBlocks)
	print 'Done'
