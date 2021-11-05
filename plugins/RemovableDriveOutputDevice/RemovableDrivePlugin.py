# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

# Python built-ins
import threading
import time

# Uranium/Messaging
from UM.Logger import Logger

# Uranium/IO
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from . import RemovableDriveOutputDevice

# Uranium/l18n
from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class RemovableDrivePlugin(OutputDevicePlugin):
    def __init__(self):
        super().__init__()

        self._update_thread = threading.Thread(target = self._updateThread)
        self._update_thread.setDaemon(True)

        self._check_updates = True

        self._drives = {}

    def start(self):
        self._update_thread.start()

    def stop(self):
        self._check_updates = False
        self._update_thread.join()

        self._addRemoveDrives({})

    def checkRemovableDrives(self):
        raise NotImplementedError()

    def ejectDevice(self, device):
        try:
            Logger.log("i", "Attempting to eject the device")
            result = self.performEjectDevice(device)
        except Exception as e:
            Logger.log("e", "Ejection failed due to: %s" % str(e))
            result = False

        if result:
            Logger.log("i", "Successfully ejected the device")
        return result

    def performEjectDevice(self, device):
        raise NotImplementedError()

    def _updateThread(self):
        while self._check_updates:
            result = self.checkRemovableDrives()
            self._addRemoveDrives(result)
            time.sleep(5)

    def _addRemoveDrives(self, drives):
        # First, find and add all new or changed keys
        for key, value in drives.items():
            if key not in self._drives:
                self.getOutputDeviceManager().addOutputDevice(RemovableDriveOutputDevice.RemovableDriveOutputDevice(key, value))
                continue

            if self._drives[key] != value:
                self.getOutputDeviceManager().removeOutputDevice(key)
                self.getOutputDeviceManager().addOutputDevice(RemovableDriveOutputDevice.RemovableDriveOutputDevice(key, value))

        # Then check for keys that have been removed
        for key in self._drives.keys():
            if key not in drives:
                self.getOutputDeviceManager().removeOutputDevice(key)

        self._drives = drives
