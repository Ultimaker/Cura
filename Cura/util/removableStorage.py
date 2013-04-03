import platform
import string
import glob
import os
import stat

def getPossibleSDcardDrives():
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

				drives.append(('%s (%s:)' % (volumeName, letter), letter + ':/', volumeName))
			bitmask >>= 1
	elif platform.system() == "Darwin":
		for volume in glob.glob('/Volumes/*'):
			if stat.S_ISLNK(os.lstat(volume).st_mode):
				continue
			#'Ejectable: Yes' in os.system('diskutil info \'%s\'' % (volume))
			drives.append((os.path.basename(volume), os.path.basename(volume), volume))
	else:
		for volume in glob.glob('/media/*'):
			drives.append((os.path.basename(volume), os.path.basename(volume), volume))
	return drives

