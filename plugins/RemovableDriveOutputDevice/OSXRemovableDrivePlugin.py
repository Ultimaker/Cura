# Copyright (c) 2015 Ultimaker B.V.
# Copyright (c) 2013 David Braam
# Uranium is released under the terms of the AGPLv3 or higher.

from . import RemovableDrivePlugin

from UM.Logger import Logger

import subprocess
import os

import plistlib

## Support for removable devices on Mac OSX
class OSXRemovableDrivePlugin(RemovableDrivePlugin.RemovableDrivePlugin):
    def checkRemovableDrives(self):
        drives = {}
        p = subprocess.Popen(["system_profiler", "SPUSBDataType", "-xml"], stdout=subprocess.PIPE)
        plist = plistlib.loads(p.communicate()[0])
        p.wait()

        for dev in self._findInTree(plist, "Mass Storage Device"):
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
        Logger.log("d", "umount returned: %s.", repr(output))

        return_code = p.wait()
        if return_code != 0:
            return False
        else:
            return True
    
    def _findInTree(self, t, n):
        ret = []
        if type(t) is dict:
            if "_name" in t and t["_name"] == n:
                ret.append(t)
            for k, v in t.items(): # TODO: @UnusedVariable "k"
                ret += self._findInTree(v, n)
        if type(t) is list:
            for v in t:
                ret += self._findInTree(v, n)
        return ret
