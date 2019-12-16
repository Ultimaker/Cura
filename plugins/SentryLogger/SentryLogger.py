# Copyright (c) 2019 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Logger import LogOutput
from typing import Set
from sentry_sdk import add_breadcrumb
from typing import Optional
import os

home_dir = os.path.expanduser("~")


class SentryLogger(LogOutput):
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
    
    ##  Log the message to the sentry hub as a breadcrumb
    #   \param log_type "e" (error), "i"(info), "d"(debug), "w"(warning) or "c"(critical) (can postfix with "_once")
    #   \param message String containing message to be logged
    def log(self, log_type: str, message: str) -> None:
        level = self._translateLogType(log_type)
        message = self._pruneSensitiveData(message)
        if level is None:
            if message not in self._show_once:
                level = self._translateLogType(log_type[0])
                if level is not None:
                    self._show_once.add(message)
                    add_breadcrumb(level = level, message = message)
        else:
            add_breadcrumb(level = level, message = message)

    @staticmethod
    def _pruneSensitiveData(message):
        if home_dir in message:
            message = message.replace(home_dir, "<censored_path>")
        return message

    @staticmethod
    def _translateLogType(log_type: str) -> Optional[str]:
        return SentryLogger._levels.get(log_type)
