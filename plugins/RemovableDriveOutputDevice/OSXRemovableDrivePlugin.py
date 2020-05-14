# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the LGPLv3 or higher.

from . import RemovableDrivePlugin

import subprocess
import os

import plistlib

## Support for removable devices on Mac OSX
class OSXRemovableDrivePlugin(RemovableDrivePlugin.RemovableDrivePlugin):
    def checkRemovableDrives(self):
        drives = {}
        p = subprocess.Popen(["system_profiler", "SPUSBDataType", "-xml"], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        plist = plistlib.loads(p.communicate()[0])

        result = self._recursiveSearch(plist, "removable_media")

        p = subprocess.Popen(["system_profiler", "SPCardReaderDataType", "-xml"], stdout=subprocess.PIPE, stderr = subprocess.PIPE)
        plist = plistlib.loads(p.communicate()[0])

        result.extend(self._recursiveSearch(plist, "removable_media"))

        for drive in result:
            # Ignore everything not explicitly marked as removable
            if drive["removable_media"] != "yes":
                continue

            # Ignore any removable device that does not have an actual volume
            if "volumes" not in drive or not drive["volumes"]:
                continue

            for volume in drive["volumes"]:
                if not "mount_point" in volume:
                    continue

                mount_point = volume["mount_point"]

                if "_name" in volume:
                    drive_name = volume["_name"]
                else:
                    drive_name = os.path.basename(mount_point)

                drives[mount_point] = drive_name

        return drives

    def performEjectDevice(self, device):
        p = subprocess.Popen(["diskutil", "eject", device.getId()], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        p.communicate()

        return_code = p.wait()
        if return_code != 0:
            return False
        else:
            return True

    # Recursively search for key in a plist parsed by plistlib
    def _recursiveSearch(self, plist, key):
        result = []
        for entry in plist:
            if key in entry:
                result.append(entry)
                continue

            if "_items" in entry:
                result.extend(self._recursiveSearch(entry["_items"], key))

            if "Media" in entry:
                result.extend(self._recursiveSearch(entry["Media"], key))

        return result
