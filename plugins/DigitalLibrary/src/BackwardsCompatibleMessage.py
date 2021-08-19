# Copyright (c) 2021 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.
from typing import Optional

from cura.CuraApplication import CuraApplication
from UM.Message import Message
from UM.Version import Version


def getBackwardsCompatibleMessage(text: str, title: str, message_type_str: str, lifetime: Optional[int] = 30) -> Message:
    if CuraApplication.getInstance().getAPIVersion() < Version("7.7.0"):
        return Message(text=text, title=title, lifetime=lifetime)
    else:
        message_type = Message.MessageType.NEUTRAL
        if ("MessageType." + message_type_str) in [str(item) for item in Message.MessageType]:
            message_type = Message.MessageType[message_type_str]
        return Message(text=text, title=title, lifetime=lifetime, message_type=message_type)
