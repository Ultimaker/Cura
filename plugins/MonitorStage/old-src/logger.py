from dataclasses import dataclass

class Logger:
    def __init__(self, name: str):
        self.name = name
        self.shown_messages = set()
        
    def show_message(self, message: object):
        if issubclass(type(message), LogMessage):
            print("ℹ️  " + message.content)
        elif issubclass(type(message), WarningMessage):
            for msg in self.shown_messages:
                if type(message) == type(msg):
                    # already shown
                    return
            # show `message`
            print("⚠️  "+message.content)
            self.shown_messages.add(message)
        else:
            raise NotImplementedError("Event not catched: ")
    

## MESSAGES ##

@dataclass(frozen=True)
class Message:
    content: str

## LOG MESSAGES ##

@dataclass(frozen=True)
class LogMessage(Message):
    ...

## WARNING MESSAGES ##

@dataclass(frozen=True)
class WarningMessage(Message):
    pass

@dataclass(frozen=True)
class NozzleTemperatureWarning(WarningMessage):
    def __init__(self, tool):
        super().__init__(
            f"The temperature for {tool} is too far from the target temperature."
        )

## ERROR MESSAGES ##