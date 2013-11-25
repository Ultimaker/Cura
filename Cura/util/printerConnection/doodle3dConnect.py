__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import threading
import json
import httplib as httpclient
import urllib
import time

from Cura.util.printerConnection import printerConnectionBase

#Class to connect and print files with the doodle3d.com wifi box
# Auto-detects if the Doodle3D box is available with a printer
class doodle3dConnect(printerConnectionBase.printerConnectionBase):
	def __init__(self):
		super(doodle3dConnect, self).__init__()

		self._http = None
		self._isAvailable = False
		self._printing = False
		self._fileBlocks = []
		self._blockIndex = None
		self._lineCount = 0
		self._progressLine = 0
		self._hotendTemperature = [0] * 4
		self._bedTemperature = 0

		self.checkThread = threading.Thread(target=self._doodle3Dthread)
		self.checkThread.daemon = True
		self.checkThread.start()

	#Load the file into memory for printing.
	def loadFile(self, filename):
		if self._printing:
			return
		self._fileBlocks = []
		self._lineCount = 0
		block = []
		blockSize = 0
		f = open(filename, "r")
		for line in f:
			#Strip out comments, we do not need to send comments
			if ';' in line:
				line = line[:line.index(';')]
			#Strip out whitespace at the beginning/end this saves data to send.
			line = line.strip()

			if len(line) < 1:
				continue
			self._lineCount += 1
			#Put the lines in 2k sized blocks, so we can send those blocks as http requests.
			if blockSize + len(line) > 2048:
				self._fileBlocks.append('\n'.join(block) + '\n')
				block = []
				blockSize = 0
			blockSize += len(line) + 1
			block.append(line)
		self._fileBlocks.append('\n'.join(block) + '\n')
		f.close()

	#Start printing the previously loaded file
	def startPrint(self):
		if self._printing or len(self._fileBlocks) < 1:
			return
		self._progressLine = 0
		self._blockIndex = 0
		self._printing = True

	#Abort the previously loaded print file
	def cancelPrint(self):
		if not self._printing:
			return
		if self._request('POST', '/d3dapi/printer/stop', {'gcode': 'M104 S0\nG28'}):
			self._printing = False

	def isPrinting(self):
		return self._printing

	#Amount of progression of the current print file. 0.0 to 1.0
	def printProgress(self):
		if self._lineCount < 1:
			return 0.0
		return float(d._progressLine) / float(d._lineCount)

	# Return if the printer with this connection type is available
	def isAvailable(self):
		return self._isAvailable

	# Get the connection status string. This is displayed to the user and can be used to communicate
	#  various information to the user.
	def getStatusString(self):
		return "TODO"

	def _doodle3Dthread(self):
		while True:
			stateReply = self._request('GET', '/d3dapi/printer/state')
			if stateReply is None:	#No API, wait 15 seconds before looking for Doodle3D again.
				self._isAvailable = False
				time.sleep(15)
				continue
			if not stateReply:		#API gave back an error (this can happen if the Doodle3D box is connecting to the printer)
				self._isAvailable = False
				time.sleep(5)
				continue
			self._isAvailable = True

			if stateReply['data']['state'] == 'idle':
				if self._printing:
					if self._blockIndex < len(self._fileBlocks):
						if self._request('POST', '/d3dapi/printer/print', {'gcode': self._fileBlocks[self._blockIndex], 'start': 'True', 'first': 'True'}):
							self._blockIndex += 1
					else:
						self._printing = False
			if stateReply['data']['state'] == 'printing':
				if self._printing:
					if self._blockIndex < len(self._fileBlocks):
						for n in xrange(0, 5):
							if self._blockIndex < len(self._fileBlocks):
								if self._request('POST', '/d3dapi/printer/print', {'gcode': self._fileBlocks[self._blockIndex]}):
									self._blockIndex += 1
					else:
						#If we are no longer sending new GCode delay a bit so we request the status less often.
						time.sleep(1)
					progress = self._request('GET', '/d3dapi/printer/progress')
					if progress:
						self._progressLine = progress['data']['current_line']
					temperature = self._request('GET', '/d3dapi/printer/temperature')
					if temperature:
						self._hotendTemperature[0] = temperature['data']['hotend']
						self._bedTemperature = temperature['data']['bed']
				else:
					#Got a printing state without us having send the print file, set the state to printing, but make sure we never send anything.
					progress = self._request('GET', '/d3dapi/printer/progress')
					if progress:
						self._printing = True
						self._blockIndex = len(self._fileBlocks)
						self._lineCount = progress['data']['total_lines']

	def _request(self, method, path, postData = None):
		if self._http is None:
			self._http = httpclient.HTTPConnection('draw.doodle3d.com')
		try:
			if postData is not None:
				self._http.request(method, path, urllib.urlencode(postData), {"Content-type": "application/x-www-form-urlencoded"})
			else:
				self._http.request(method, path, headers={"Content-type": "application/x-www-form-urlencoded"})
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
		print d._progressLine, d._lineCount, d._blockIndex, len(d._fileBlocks)
	print 'Done'
