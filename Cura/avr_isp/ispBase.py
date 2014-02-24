"""
General interface for Isp based AVR programmers.
The ISP AVR programmer can load firmware into AVR chips. Which are commonly used on 3D printers.

 Needs to be subclassed to support different programmers.
 Currently only the stk500v2 subclass exists.
"""
__copyright__ = "Copyright (C) 2013 David Braam - Released under terms of the AGPLv3 License"

import chipDB

class IspBase():
	"""
	Base class for ISP based AVR programmers.
	Functions in this class raise an IspError when something goes wrong.
	"""
	def programChip(self, flashData):
		""" Program a chip with the given flash data. """
		self.curExtAddr = -1
		self.chip = chipDB.getChipFromDB(self.getSignature())
		if not self.chip:
			raise IspError("Chip with signature: " + str(self.getSignature()) + "not found")
		self.chipErase()
		
		print("Flashing %i bytes" % len(flashData))
		self.writeFlash(flashData)
		print("Verifying %i bytes" % len(flashData))
		self.verifyFlash(flashData)

	def getSignature(self):
		"""
		Get the AVR signature from the chip. This is a 3 byte array which describes which chip we are connected to.
		This is important to verify that we are programming the correct type of chip and that we use proper flash block sizes.
		"""
		sig = []
		sig.append(self.sendISP([0x30, 0x00, 0x00, 0x00])[3])
		sig.append(self.sendISP([0x30, 0x00, 0x01, 0x00])[3])
		sig.append(self.sendISP([0x30, 0x00, 0x02, 0x00])[3])
		return sig
	
	def chipErase(self):
		"""
		Do a full chip erase, clears all data, and lockbits.
		"""
		self.sendISP([0xAC, 0x80, 0x00, 0x00])

	def writeFlash(self, flashData):
		"""
		Write the flash data, needs to be implemented in a subclass.
		"""
		raise IspError("Called undefined writeFlash")

	def verifyFlash(self, flashData):
		"""
		Verify the flash data, needs to be implemented in a subclass.
		"""
		raise IspError("Called undefined verifyFlash")

class IspError():
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
