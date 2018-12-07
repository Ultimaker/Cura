# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from datetime import datetime, timezone

from ...Models import BaseModel


class BaseCloudModel(BaseModel):
    def __eq__(self, other):
        return type(self) == type(other) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return type(self) != type(other) or self.__dict__ != other.__dict__

    @staticmethod
    def parseDate(date_str: str) -> datetime:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
