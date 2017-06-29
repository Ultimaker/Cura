# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the AGPLv3 or higher.


from UM.Job import Job
from UM.Logger import Logger
from UM.Platform import Platform

import ssl
import urllib.request
import urllib.error

from typing import Any


class SliceInfoJob(Job):
    data = None  # type: Any
    url = None  # type: str

    def __init__(self, url, data):
        super().__init__()
        self.url = url
        self.data = data

    def run(self):
        if not self.url or not self.data:
            Logger.log("e", "URL or DATA for sending slice info was not set!")
            return

        # Submit data
        kwoptions = {"data" : self.data,
                     "timeout" : 5
                     }

        if Platform.isOSX():
            kwoptions["context"] = ssl._create_unverified_context()

        Logger.log("d", "Sending anonymous slice info to [%s]...", self.url)

        try:
            f = urllib.request.urlopen(self.url, **kwoptions)
            Logger.log("i", "Sent anonymous slice info.")
            f.close()
        except urllib.error.HTTPError as http_exception:
            Logger.log("e", "An HTTP error occurred while trying to send slice information: %s" % http_exception)
        except Exception as e: # We don't want any exception to cause problems
            Logger.log("e", "An exception occurred while trying to send slice information: %s" % e)