import platform
import string
import glob
import os
import stat
import time
import subprocess
try:
	from xml.etree import cElementTree as ElementTree
except:
	from xml.etree import ElementTree

_removeableCache = None
_removeableCacheTime = None

def _parseStupidPListXML(e):
	if e.tag == 'plist':
		return _parseStupidPListXML(list(e)[0])
	if e.tag == 'array':
		ret = []
		for c in list(e):
			ret.append(_parseStupidPListXML(c))
		return ret
	if e.tag == 'dict':
		ret = {}
		key = None
		for c in list(e):
			if c.tag == 'key':
				key = c.text
			elif key is not None:
				ret[key] = _parseStupidPListXML(c)
				key = None
		return ret
	if e.tag == 'true':
		return True
	if e.tag == 'false':
		return False
	return e.text

def _findInTree(t, n):
	ret = []
	if type(t) is dict:
		if '_name' in t and t['_name'] == n:
			ret.append(t)
		for k, v in t.items():
			ret += _findInTree(v, n)
	if type(t) is list:
		for v in t:
			ret += _findInTree(v, n)
	return ret

def getPossibleSDcardDrives():
	global _removeableCache, _removeableCacheTime
	if _removeableCache is not None and time.time() - _removeableCacheTime < 5.0:
		return _removeableCache

	drives = []
	if platform.system() == "Windows":
		from ctypes import windll
		import ctypes
		bitmask = windll.kernel32.GetLogicalDrives()
		for letter in string.uppercase:
			if bitmask & 1 and windll.kernel32.GetDriveTypeA(letter + ':/') == 2:
				volumeName = ''
				nameBuffer = ctypes.create_unicode_buffer(1024)
				if windll.kernel32.GetVolumeInformationW(ctypes.c_wchar_p(letter + ':/'), nameBuffer, ctypes.sizeof(nameBuffer), None, None, None, None, 0) == 0:
					volumeName = nameBuffer.value
				if volumeName == '':
					volumeName = 'NO NAME'

				freeBytes = ctypes.c_longlong(0)
				if windll.kernel32.GetDiskFreeSpaceExA(letter + ':/', ctypes.byref(freeBytes), None, None) == 0:
					continue
				if freeBytes.value < 1:
					continue
				drives.append(('%s (%s:)' % (volumeName, letter), letter + ':/', volumeName))
			bitmask >>= 1
	elif platform.system() == "Darwin":
		p = subprocess.Popen(['system_profiler', 'SPUSBDataType', '-xml'], stdout=subprocess.PIPE)
		xml = ElementTree.fromstring(p.communicate()[0])
		p.wait()

		xml = _parseStupidPListXML(xml)
		for dev in _findInTree(xml, 'Mass Storage Device'):
			if 'removable_media' in dev and dev['removable_media'] == 'yes' and 'volumes' in dev and len(dev['volumes']) > 0:
				for vol in dev['volumes']:
					if 'mount_point' in vol:
						volume = vol['mount_point']
						drives.append((os.path.basename(volume), volume, os.path.basename(volume)))
	else:
		for volume in glob.glob('/media/*'):
			drives.append((os.path.basename(volume), volume, os.path.basename(volume)))

	_removeableCache = drives
	_removeableCacheTime = time.time()
	return drives

def ejectDrive(driveName):
	if platform.system() == "Windows":
		cmd = '"%s" %s>NUL' % (os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'EjectMedia.exe')), driveName)
	elif platform.system() == "Darwin":
		cmd = "diskutil eject '%s' > /dev/null 2>&1" % (driveName)
	else:
		cmd = "umount '%s' > /dev/null 2>&1" % (driveName)
	if os.system(cmd):
		return False
	else:
		return True

if __name__ == '__main__':
	print getPossibleSDcardDrives()
