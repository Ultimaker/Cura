import platform
import string
import glob
import os
import stat

def getPossibleSDcardDrives():
	drives = []
	if platform.system() == "Windows":
		from ctypes import windll
		bitmask = windll.kernel32.GetLogicalDrives()
		for letter in string.uppercase:
			if bitmask & 1 and windll.kernel32.GetDriveTypeA(letter + ':/') == 2:
				drives.append(letter + ':/')
			bitmask >>= 1
	elif platform.system() == "Darwin":
		for volume in glob.glob('/Volumes/*'):
			if stat.S_ISLNK(os.lstat(volume).st_mode):
				continue
			#'Ejectable: Yes' in os.system('diskutil info \'%s\'' % (volume))
			drives.append(volume)
	else:
		for volume in glob.glob('/media/*'):
			drives.append(volume)
	return drives

