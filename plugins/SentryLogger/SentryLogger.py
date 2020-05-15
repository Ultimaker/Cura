# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import LogOutput
from typing import Set

from cura.CrashHandler import CrashHandler

try:
    from sentry_sdk import add_breadcrumb
except ImportError:
    pass
from typing import Optional
import os


class SentryLogger(LogOutput):
    # Sentry (https://sentry.io) is the service that Cura uses for logging crashes. This logger ensures that the
    # regular log entries that we create are added as breadcrumbs so when a crash actually happens, they are already
    # processed and ready for sending.
    # Note that this only prepares them for sending. It only sends them when the user actually agrees to sending the
    # information.
    
    _levels = {
        "w": "warning",
        "i": "info",
        "c": "fatal",
        "e": "error",
        "d": "debug"
    }

    def __init__(self) -> None:
        super().__init__()
        self._show_once = set()  # type: Set[str]
    
    def log(self, log_type: str, message: str) -> None:
        """Log the message to the sentry hub as a breadcrumb
        
        :param log_type: "e" (error), "i"(info), "d"(debug), "w"(warning) or "c"(critical) (can postfix with "_once")
        :param message: String containing message to be logged
        """
        level = self._translateLogType(log_type)
        message = CrashHandler.pruneSensitiveData(message)
        if level is None:
            if message not in self._show_once:
                level = self._translateLogType(log_type[0])
                if level is not None:
                    self._show_once.add(message)
                    add_breadcrumb(level = level, message = message)
        else:
            add_breadcrumb(level = level, message = message)

    @staticmethod
    def _translateLogType(log_type: str) -> Optional[str]:
        return SentryLogger._levels.get(log_type)
