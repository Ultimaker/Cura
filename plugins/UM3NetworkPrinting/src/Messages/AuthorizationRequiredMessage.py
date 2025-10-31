# Copyright (c) 2025 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Message import Message


class AuthorizationRequiredMessage:

    _inner_message_instance = None
    class InnerMessage(Message):
        def __init__(self, printer_name: str, err_message: str) -> None:
            super().__init__(
                text = printer_name,
                title = err_message,
                message_type = Message.MessageType.WARNING,
                lifetime = 0
            )

    @classmethod
    def _getInstance(cls) -> Message:
        if cls._inner_message_instance is None:
            cls._inner_message_instance = cls.InnerMessage("", "")
        return cls._inner_message_instance

    @classmethod
    def show(cls, printer_name: str, err_message: str) -> None:
        msg = cls._getInstance()
        msg.setText(printer_name)
        msg.setTitle(err_message)
        msg.show()

    @classmethod
    def hide(cls) -> None:
        cls._getInstance().hide()
