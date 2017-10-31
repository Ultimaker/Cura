# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from UM.Job import Job
from UM.Logger import Logger
from UM.Platform import Platform

import ssl
import urllib.request
import urllib.error


class SliceInfoJob(Job):
    def __init__(self, url, data):
        super().__init__()
        self._url = url
        self._data = data

    def run(self):
        if not self._url or not self._data:
            Logger.log("e", "URL or DATA for sending slice info was not set!")
            return

        # Submit data
        kwoptions = {"data" : self._data, "timeout" : 5}

        if Platform.isOSX():
            kwoptions["context"] = ssl._create_unverified_context()

        Logger.log("i", "Sending anonymous slice info to [%s]...", self._url)

        try:
            f = urllib.request.urlopen(self._url, **kwoptions)
            Logger.log("i", "Sent anonymous slice info.")
            f.close()
        except urllib.error.HTTPError:
            Logger.logException("e", "An HTTP error occurred while trying to send slice information")
        except Exception:  # We don't want any exception to cause problems
            Logger.logException("e", "An exception occurred while trying to send slice information")