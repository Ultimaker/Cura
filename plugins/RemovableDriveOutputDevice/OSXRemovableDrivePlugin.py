# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the AGPLv3 or higher.

from . import RemovableDrivePlugin

import threading

import subprocess
import time
import os

import plistlib

## Support for removable devices on Mac OSX
class OSXRemovableDrivePlugin(RemovableDrivePlugin.RemovableDrivePlugin):
    def checkRemovableDrives(self):
        drives = {}
        p = subprocess.Popen(["system_profiler", "SPUSBDataType", "-xml"], stdout = subprocess.PIPE)
        plist = plistlib.loads(p.communicate()[0])
        p.wait()

        for entry in plist:
            if "_items" in entry:
                for item in entry["_items"]:
                    for dev in item["_items"]:
                        if "removable_media" in dev and dev["removable_media"] == "yes" and "volumes" in dev and len(dev["volumes"]) > 0:
                            for vol in dev["volumes"]:
                                if "mount_point" in vol:
                                    volume = vol["mount_point"]
                                    drives[volume] = os.path.basename(volume)

        p = subprocess.Popen(["system_profiler", "SPCardReaderDataType", "-xml"], stdout=subprocess.PIPE)
        plist = plistlib.loads(p.communicate()[0])
        p.wait()

        for entry in plist:
            if "_items" in entry:
                for item in entry["_items"]:
                    for dev in item["_items"]:
                        if "removable_media" in dev and dev["removable_media"] == "yes" and "volumes" in dev and len(dev["volumes"]) > 0:
                            for vol in dev["volumes"]:
                                if "mount_point" in vol:
                                    volume = vol["mount_point"]
                                    drives[volume] = os.path.basename(volume)

        return drives

    def performEjectDevice(self, device):
        p = subprocess.Popen(["diskutil", "eject", device.getId()], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        output = p.communicate()

        return_code = p.wait()
        if return_code != 0:
            return False
        else:
            return True