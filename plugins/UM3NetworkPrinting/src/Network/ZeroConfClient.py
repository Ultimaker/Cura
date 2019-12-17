# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from queue import Queue
from threading import Thread, Event
from time import time
from typing import Optional

from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange, ServiceInfo

from UM.Logger import Logger
from UM.Signal import Signal
from cura.CuraApplication import CuraApplication


## The ZeroConfClient handles all network discovery logic.
#  It emits signals when new network services were found or disappeared.
class ZeroConfClient:

    # The discovery protocol name for Ultimaker printers.
    ZERO_CONF_NAME = u"_ultimaker._tcp.local."

    # Signals emitted when new services were discovered or removed on the network.
    addedNetworkCluster = Signal()
    removedNetworkCluster = Signal()

    def __init__(self) -> None:
        self._zero_conf = None  # type: Optional[Zeroconf]
        self._zero_conf_browser = None  # type: Optional[ServiceBrowser]
        self._service_changed_request_queue = None  # type: Optional[Queue]
        self._service_changed_request_event = None  # type: Optional[Event]
        self._service_changed_request_thread = None  # type: Optional[Thread]

    ## The ZeroConf service changed requests are handled in a separate thread so we don't block the UI.
    #  We can also re-schedule the requests when they fail to get detailed service info.
    #  Any new or re-reschedule requests will be appended to the request queue and the thread will process them.
    def start(self) -> None:
        self._service_changed_request_queue = Queue()
        self._service_changed_request_event = Event()
        try:
            self._zero_conf = Zeroconf()
        # CURA-6855 catch WinErrors
        except OSError:
            Logger.logException("e", "Failed to create zeroconf instance.")
            return

        self._service_changed_request_thread = Thread(target = self._handleOnServiceChangedRequests, daemon = True)
        self._service_changed_request_thread.start()
        self._zero_conf_browser = ServiceBrowser(self._zero_conf, self.ZERO_CONF_NAME, [self._queueService])

    # Cleanup ZeroConf resources.
    def stop(self) -> None:
        if self._zero_conf is not None:
            self._zero_conf.close()
            self._zero_conf = None
        if self._zero_conf_browser is not None:
            self._zero_conf_browser.cancel()
            self._zero_conf_browser = None

    ## Handles a change is discovered network services.
    def _queueService(self, zeroconf: Zeroconf, service_type, name: str, state_change: ServiceStateChange) -> None:
        item = (zeroconf, service_type, name, state_change)
        if not self._service_changed_request_queue or not self._service_changed_request_event:
            return
        self._service_changed_request_queue.put(item)
        self._service_changed_request_event.set()

    ## Callback for when a ZeroConf service has changes.
    def _handleOnServiceChangedRequests(self) -> None:
        if not self._service_changed_request_queue or not self._service_changed_request_event:
            return

        while True:
            # Wait for the event to be set
            self._service_changed_request_event.wait(timeout=5.0)

            # Stop if the application is shutting down
            if CuraApplication.getInstance().isShuttingDown():
                return

            self._service_changed_request_event.clear()

            # Handle all pending requests
            reschedule_requests = []  # A list of requests that have failed so later they will get re-scheduled
            while not self._service_changed_request_queue.empty():
                request = self._service_changed_request_queue.get()
                zeroconf, service_type, name, state_change = request
                try:
                    result = self._onServiceChanged(zeroconf, service_type, name, state_change)
                    if not result:
                        reschedule_requests.append(request)
                except Exception:
                    Logger.logException("e", "Failed to get service info for [%s] [%s], the request will be rescheduled",
                                        service_type, name)
                    reschedule_requests.append(request)

            # Re-schedule the failed requests if any
            if reschedule_requests:
                for request in reschedule_requests:
                    self._service_changed_request_queue.put(request)

    ##  Handler for zeroConf detection.
    #   Return True or False indicating if the process succeeded.
    #   Note that this function can take over 3 seconds to complete. Be careful calling it from the main thread.
    def _onServiceChanged(self, zero_conf: Zeroconf, service_type: str, name: str, state_change: ServiceStateChange
                          ) -> bool:
        if state_change == ServiceStateChange.Added:
            return self._onServiceAdded(zero_conf, service_type, name)
        elif state_change == ServiceStateChange.Removed:
            return self._onServiceRemoved(name)
        return True

    ## Handler for when a ZeroConf service was added.
    def _onServiceAdded(self, zero_conf: Zeroconf, service_type: str, name: str) -> bool:
        # First try getting info from zero-conf cache
        info = ServiceInfo(service_type, name, properties={})
        for record in zero_conf.cache.entries_with_name(name.lower()):
            info.update_record(zero_conf, time(), record)

        for record in zero_conf.cache.entries_with_name(info.server):
            info.update_record(zero_conf, time(), record)
            if info.address:
                break

        # Request more data if info is not complete
        if not info.address:
            new_info = zero_conf.get_service_info(service_type, name)
            if new_info is not None:
                info = new_info

        if info:
            type_of_device = info.properties.get(b"type", None)
            if type_of_device:
                if type_of_device == b"printer":
                    address = '.'.join(map(lambda n: str(n), info.address))
                    self.addedNetworkCluster.emit(str(name), address, info.properties)
                else:
                    Logger.log("w", "The type of the found device is '%s', not 'printer'." % type_of_device)
        else:
            Logger.log("w", "Could not get information about %s" % name)
            return False

        return True

    ## Handler for when a ZeroConf service was removed.
    def _onServiceRemoved(self, name: str) -> bool:
        Logger.log("d", "ZeroConf service removed: %s" % name)
        self.removedNetworkCluster.emit(str(name))
        return True
