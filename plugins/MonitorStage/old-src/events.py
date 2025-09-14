from dataclasses import dataclass

# Base Event class (optional, but good for type hinting)
@dataclass(frozen=True) # frozen=True makes them immutable and hashable
class Event:
    pass

@dataclass(frozen=True)
class UpdateNozzleTemperature(Event):
    tool: str          # e.g. "T0", "T1"
    temperature: float # current temperature of that tool

@dataclass(frozen=True)
class UpdateTargetTemperature(Event):
    tool: str          # e.g. "T0", "T1"
    temperature: float # target temperature for that tool

@dataclass(frozen=True)
class NewGcodeFileHandler(Event):
    handler: object

@dataclass(frozen=True)
class SetGcodeLine(Event):
    line: int

@dataclass(frozen=True)
class NewGcodeFile(Event):
    filename: str

#
@dataclass(frozen=True)
class Jog(Event):
    movement: list # [delta_x, delta_y, delta_z, delta_z]


@dataclass(frozen=True)
class Home(Event):
    ...


# GCODE ACTIONS

@dataclass(frozen=True)
class PlayGcode(Event):
    ...

@dataclass(frozen=True)
class PauseGcode(Event):
    ...

@dataclass(frozen=True)
class ArduinoConnected(Event):
    ...

@dataclass(frozen=True)
class ArduinoDisconnected(Event):
    ...
