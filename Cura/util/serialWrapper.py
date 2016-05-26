# Serial wrapper around pyserial that adds support for custom baudrates (250000)
# on linux, when pyserial is < 2.7

# This code was copied from the pyserial 2.7 base code.
# Therefore, it follows the license used by pyserial which is the '3-clause BSD license'

from serial import *
import sys

if sys.platform.startswith('linux'):
	import serial.serialposix

	try:
		import pkg_resources

		old_version = float(pkg_resources.get_distribution("pyserial").version) < 2.7
	except:
		old_version = True

	if old_version and not hasattr(serial.serialposix, "TCGETS2") and \
	   hasattr(serial.serialposix, "set_special_baudrate"):
		# Detected pyserial < 2.7 which doesn't support custom baudrates
		# Replacing set_special_baudrate with updated function from pyserial 2.7

		TCGETS2 = 0x802C542A
		TCSETS2 = 0x402C542B
		BOTHER = 0o010000

		def set_special_baudrate(port, baudrate):
			# right size is 44 on x86_64, allow for some growth
			import array
			buf = array.array('i', [0] * 64)

			try:
				# get serial_struct
				FCNTL.ioctl(port.fd, TCGETS2, buf)
				# set custom speed
				buf[2] &= ~TERMIOS.CBAUD
				buf[2] |= BOTHER
				buf[9] = buf[10] = baudrate

				# set serial_struct
				res = FCNTL.ioctl(port.fd, TCSETS2, buf)
			except IOError, e:
				raise ValueError('Failed to set custom baud rate (%s): %s' % (baudrate, e))

		# We need to change the function inside the serialposix module otherwise, it won't
		# be called by the code within that module
		serial.serialposix.set_special_baudrate = set_special_baudrate
