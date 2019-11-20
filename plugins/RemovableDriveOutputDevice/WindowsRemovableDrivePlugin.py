# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the LGPLv3 or higher.
from . import RemovableDrivePlugin

import string
import ctypes
from ctypes import wintypes  # Using ctypes.wintypes in the code below does not seem to work

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

# Ignore windows error popups. Fixes the whole "Can't open drive X" when user has an SD card reader.
ctypes.windll.kernel32.SetErrorMode(1) #type: ignore

# WinAPI Constants that we need
# Hardcoded here due to stupid WinDLL stuff that does not give us access to these values.
DRIVE_REMOVABLE = 2 # [CodeStyle: Windows Enum value]

GENERIC_READ = 2147483648 # [CodeStyle: Windows Enum value]
GENERIC_WRITE = 1073741824 # [CodeStyle: Windows Enum value]

FILE_SHARE_READ = 1 # [CodeStyle: Windows Enum value]
FILE_SHARE_WRITE = 2 # [CodeStyle: Windows Enum value]

IOCTL_STORAGE_EJECT_MEDIA = 2967560 # [CodeStyle: Windows Enum value]

OPEN_EXISTING = 3 # [CodeStyle: Windows Enum value]

# Setup the DeviceIoControl function arguments and return type.
# See ctypes documentation for details on how to call C functions from python, and why this is important.
ctypes.windll.kernel32.DeviceIoControl.argtypes = [ #type: ignore
    wintypes.HANDLE,                    # _In_          HANDLE hDevice
    wintypes.DWORD,                     # _In_          DWORD dwIoControlCode
    wintypes.LPVOID,                    # _In_opt_      LPVOID lpInBuffer
    wintypes.DWORD,                     # _In_          DWORD nInBufferSize
    wintypes.LPVOID,                    # _Out_opt_     LPVOID lpOutBuffer
    wintypes.DWORD,                     # _In_          DWORD nOutBufferSize
    ctypes.POINTER(wintypes.DWORD),     # _Out_opt_     LPDWORD lpBytesReturned
    wintypes.LPVOID                     # _Inout_opt_   LPOVERLAPPED lpOverlapped
]
ctypes.windll.kernel32.DeviceIoControl.restype = wintypes.BOOL #type: ignore


## Removable drive support for windows
class WindowsRemovableDrivePlugin(RemovableDrivePlugin.RemovableDrivePlugin):
    def checkRemovableDrives(self):
        drives = {}

        bitmask = ctypes.windll.kernel32.GetLogicalDrives()
        # Check possible drive letters, from C to Z
        # Note: using ascii_uppercase because we do not want this to change with locale!
        # Skip A and B, since those drives are typically reserved for floppy disks.
        # Those drives can theoretically be reassigned but it's safer to not check them for removable drives.
        # Windows will also behave weirdly even with some of its internal functions if you do this (e.g. search indexing doesn't search it).
        # Users that have removable drives in A or B will just have to save to file and select the drive there.
        for letter in string.ascii_uppercase[2:]:
            drive = "{0}:/".format(letter)

            # Do we really want to skip A and B?
            # GetDriveTypeA explicitly wants a byte array of type ascii. It will accept a string, but this wont work
            if bitmask & 1 and ctypes.windll.kernel32.GetDriveTypeA(drive.encode("ascii")) == DRIVE_REMOVABLE:
                volume_name = ""
                name_buffer = ctypes.create_unicode_buffer(1024)
                filesystem_buffer = ctypes.create_unicode_buffer(1024)
                error = ctypes.windll.kernel32.GetVolumeInformationW(ctypes.c_wchar_p(drive), name_buffer, ctypes.sizeof(name_buffer), None, None, None, filesystem_buffer, ctypes.sizeof(filesystem_buffer))

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
                free_bytes = ctypes.c_longlong(0)
                if ctypes.windll.kernel32.GetDiskFreeSpaceExA(drive.encode("ascii"), ctypes.byref(free_bytes), None, None) == 0:
                    continue

                if free_bytes.value < 1:
                    continue

                drives[drive] = "{0} ({1}:)".format(volume_name, letter)
            bitmask >>= 1

        return drives

    def performEjectDevice(self, device):
        # Magic WinAPI stuff
        # First, open a handle to the Device
        handle = ctypes.windll.kernel32.CreateFileA("\\\\.\\{0}".format(device.getId()[:-1]).encode("ascii"), GENERIC_READ | GENERIC_WRITE, FILE_SHARE_READ | FILE_SHARE_WRITE, None, OPEN_EXISTING, 0, None )

        if handle == -1:
            # ctypes.WinError sets up an GetLastError API call for windows as an Python OSError exception.
            # So we use this to raise the error to our caller.
            raise ctypes.WinError()

        # The DeviceIoControl requires a bytes_returned pointer to be a valid pointer.
        # So create a ctypes DWORD to reference. (Without this pointer the DeviceIoControl function will crash with an access violation after doing its job.
        bytes_returned = wintypes.DWORD(0)

        error = None

        # Then, try and tell it to eject
        return_code = ctypes.windll.kernel32.DeviceIoControl(handle, IOCTL_STORAGE_EJECT_MEDIA, None, 0, None, 0, ctypes.pointer(bytes_returned), None)
        # DeviceIoControl with IOCTL_STORAGE_EJECT_MEDIA return 0 on error.
        if return_code == 0:
            # ctypes.WinError sets up an GetLastError API call for windows as an Python OSError exception.
            # So we use this to raise the error to our caller.
            error = ctypes.WinError()
            # Do not raise an error here yet, so we can properly close the handle.

        # Finally, close the handle
        ctypes.windll.kernel32.CloseHandle(handle)

        # If an error happened in the DeviceIoControl, raise it now.
        if error:
            raise error

        # Return success
        return True