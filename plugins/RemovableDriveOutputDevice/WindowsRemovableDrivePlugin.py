# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the AGPLv3 or higher.

from . import RemovableDrivePlugin

import threading
import string

from ctypes import windll
from ctypes import wintypes

import ctypes
import time
import os
import subprocess

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

# WinAPI Constants that we need
# Hardcoded here due to stupid WinDLL stuff that does not give us access to these values.
DRIVE_REMOVABLE = 2

GENERIC_READ = 2147483648
GENERIC_WRITE = 1073741824

FILE_SHARE_READ = 1
FILE_SHARE_WRITE = 2

IOCTL_STORAGE_EJECT_MEDIA = 2967560

OPEN_EXISTING = 3

## Removable drive support for windows
class WindowsRemovableDrivePlugin(RemovableDrivePlugin.RemovableDrivePlugin):
    def checkRemovableDrives(self):
        drives = {}

        bitmask = windll.kernel32.GetLogicalDrives()
        # Check possible drive letters, from A to Z
        # Note: using ascii_uppercase because we do not want this to change with locale!
        for letter in string.ascii_uppercase:
            drive = "{0}:/".format(letter)

            # Do we really want to skip A and B?
            # GetDriveTypeA explicitly wants a byte array of type ascii. It will accept a string, but this wont work
            if bitmask & 1 and windll.kernel32.GetDriveTypeA(drive.encode("ascii")) == DRIVE_REMOVABLE:
                volume_name = ""
                name_buffer = ctypes.create_unicode_buffer(1024)
                filesystem_buffer = ctypes.create_unicode_buffer(1024)
                error = windll.kernel32.GetVolumeInformationW(ctypes.c_wchar_p(drive), name_buffer, ctypes.sizeof(name_buffer), None, None, None, filesystem_buffer, ctypes.sizeof(filesystem_buffer))

                if error != 0:
                    volume_name = name_buffer.value

                if not volume_name:
                    volume_name = catalog.i18nc("@item:intext", "Removable Drive")

                # Certain readers will report themselves as a volume even when there is no card inserted, but will show an
                # "No volume in drive" warning when trying to call GetDiskFreeSpace. However, they will not report a valid
                # filesystem, so we can filter on that. In addition, this excludes other things with filesystems Windows
                # does not support.
                if filesystem_buffer.value == "":
                    continue

                # Check for the free space. Some card readers show up as a drive with 0 space free when there is no card inserted.
                freeBytes = ctypes.c_longlong(0)
                if windll.kernel32.GetDiskFreeSpaceExA(drive.encode("ascii"), ctypes.byref(freeBytes), None, None) == 0:
                    continue

                if freeBytes.value < 1:
                    continue

                drives[drive] = "{0} ({1}:)".format(volume_name, letter)
            bitmask >>= 1

        return drives

    def performEjectDevice(self, device):
        # Magic WinAPI stuff
        # First, open a handle to the Device
        handle = windll.kernel32.CreateFileA("\\\\.\\{0}".format(device.getId()[:-1]).encode("ascii"), GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None )

        if handle == -1:
            print(windll.kernel32.GetLastError())
            return

        result = None
        # Then, try and tell it to eject
        if not windll.kernel32.DeviceIoControl(handle, IOCTL_STORAGE_EJECT_MEDIA, None, None, None, None, None, None):
            result = False
        else:
            result = True

        # Finally, close the handle
        windll.kernel32.CloseHandle(handle)
        return result
