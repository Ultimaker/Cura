# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.


## The network API client is responsible for handling requests and responses to printer over the local network (LAN).
class NetworkApiClient:

    API_PREFIX = "/cluster-api/v1/"

    def __init__(self) -> None:
        pass

    def getPrinters(self):
        pass

    def getPrintJobs(self):
        pass

    def requestPrint(self):
        pass

    def doPrintJobAction(self):
        pass
