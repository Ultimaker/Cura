# Copyright (c) 2023 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

import json

from typing import List, Dict, Tuple, Any, Optional, Union
from math import pi

from numpy import zeros, isfinite
from numpy.linalg import norm

from cura.CuraApplication import CuraApplication

machine_lut = {"Makerbot Replicator mini": 'mini_8',
               "Makerbot Replicator 5th Gen": 'replicator_5',
               "Makerbot Replicator Z18": 'z18_6',
               "Makerbot Replicator+": 'replicator_b',
               "Makerbot Sketch": 'sketch',
               "Makerbot Sketch Large": 'sketch_large',
               "Makerbot Method": 'fire_e',
               "Makerbot Method X": 'lava_f',
               "Makerbot Method XL": 'magma_10'
               }

extruder_lut = {"Makerbot Replicator mini": 'mk13',
                "Makerbot Replicator 5th Gen": 'mk13',
                "Makerbot Replicator Z18": 'mk13',
                "Makerbot Replicator+": 'mk13',
                "Makerbot Sketch": 'sketch_extruder',
                "Makerbot Sketch Large": 'sketch_l_extruder'
                }

material_lut = {'2780b345-577b-4a24-a2c5-12e6aad3e690': 'abs',
                '88c8919c-6a09-471a-b7b6-e801263d862d': 'abs-wss1',
                '416eead4-0d8e-4f0b-8bfc-a91a519befa5': 'asa',
                '85bbae0e-938d-46fb-989f-c9b3689dc4f0': 'nylon-cf',
                '283d439a-3490-4481-920c-c51d8cdecf9c': 'nylon',
                '62414577-94d1-490d-b1e4-7ef3ec40db02': 'pc',
                '69386c85-5b6c-421a-bec5-aeb1fb33f060': 'pet',  # PETG
                '0ff92885-617b-4144-a03c-9989872454bc': 'pla',
                'a4255da2-cb2a-4042-be49-4a83957a2f9a': 'pva',
                'a140ef8f-4f26-4e73-abe0-cfc29d6d1024': 'wss1',
                '77873465-83a9-4283-bc44-4e542b8eb3eb': 'sr30',
                '96fca5d9-0371-4516-9e96-8e8182677f3c': 'im-pla',
                '19baa6a9-94ff-478b-b4a1-8157b74358d2': 'tpu',
                }

printhead_lut = {'1A': 'mk14',
                 '1XA': 'mk14_hot',
                 '1C': 'mk14_c',
                 '2A': 'mk14_s',
                 '2XA': 'mk14_hot_s',
                 'Lab': 'mk14_e',
                 'S+': 'mk13',
                 'EE': 'mk13_experimental',
                 'TS+': 'mk13_impla',
                 'SKT': 'sketch_extruder',
                 }

tags_lut = {"WALL-OUTER": ['Inset'],  # 'Inset',
            "WALL-INNER": ['Inset'],
            "SKIN": ["Fill Roof Surface", "Roof"],
            "FILL": ['Infill', "Sparse"],
            "SUPPORT": ['Support'],
            "SUPPORT-INTERFACE": ['Support', 'Roof'],
            "PRIME-TOWER": ['Purge'],
            "SKIRT": ['Purge'],
            "TRAVEL": ['Travel Move'],  # Note: these are not cura comments but will be calculated
            "RETRACT": ['Retract'],
            "UNRETRACT": ['Restart'],
            # 'Leaky Travel Move',
            # 'Long Retract',
            # 'Long Restart',
            # 'Trailing Extrusion Move'
            # 'Z Hop'
            # 'Un Z Hop'
            # 'Wipe Extruder'
            # 'Raft'
            # 'Fill Roof Surface'
            # 'Floor'
            # 'Wait for Temperature'
            # 'Quick Toggle'
            # 'Solid'
            # 'Sparse'
            }

bead_lut = {"WALL-OUTER": 'BeadMode External',
            "SKIN": 'BeadMode External',
            "WALL-INNER": 'BeadMode Internal Thick',
            "FILL": 'BeadMode User3',
            "SUPPORT": 'BeadMode Internal Thick',
            "SUPPORT-INTERFACE": 'BeadMode External',
            "PRIME-TOWER": 'BeadMode User1',
            "SKIRT": 'BeadMode User1',
            "RAFT": 'BeadMode User1',
            }


def move(x: float, y: float, z: float, a: float, b: float, feedrate: float, tags: Optional[List[str]] = None) -> Dict[
    str, Any]:
    """ Create a move (G0 or G1) in Makerbot json format
        The 0,0 point is in the middle of the build plate iso of the left front.
        This does not look nice in Cura because the xyz coordinate system will be displayed in the middle of the print.
        Therefore, we pretent this system has a coordinate 0,0 in the left front (setting) and offset the coordinates
        to the center at x,y = 75,95
    """
    if tags is None:
        tags = []
    return {"command": {'function': "move",
                        "metadata": {"relative": {"a": True, "b": True, "x": False, "y": False, "z": False}},
                        "parameters": {"a": a,
                                       "b": b,
                                       "feedrate": feedrate,
                                       "x": x,  # x - 75,
                                       "y": y,  # y - 95,
                                       "z": z},
                        "tags": tags}}


def comment(comment: str, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """ Create a comment (metadata) in Makerbot json format
        Mainly used to create layer section information to display in the viewer
    """
    if tags is None:
        tags = []
    return {"command": {"function": "comment",
                        "metadata": {},
                        "parameters": {"comment": f"{comment}"},
                        "tags": tags}}


def set_toolhead_temperature(index: int, temperature: float, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """ Set the print head temperature setpoint (M104 or M109) in Makerbot json format """
    if tags is None:
        tags = []
    return {"command": {"function": "set_toolhead_temperature",
                        "metadata": {},
                        "parameters": {"index": index, "temperature": temperature},
                        "tags": tags}}


def wait_for_temperature(index: int, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """ Wait for the print head temperature to reach its setpoint (M109) in Makerbot json format """
    if tags is None:
        tags = []
    return {"command": {"function": "wait_for_temperature",
                        "metadata": {},
                        "parameters": {"index": index},
                        "tags": tags}}


def change_toolhead(index: int, x: float, y: float, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """ Switch tool (T0 or T1) in Makerbot json format """
    if tags is None:
        tags = []
    return {"command": {"function": "change_toolhead",
                        "metadata": {},
                        "parameters": {"index": index, "x": x, "y": y},
                        "tags": tags},
            }


def toggle_fan(index: int, value: bool, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """ Toggle the cold end/heat break cooling fans per print head.
        Note that these are NOT the object cooling fans (blowing onto the print).
        Makerbot has a cold end fan per print head and switches the cold end cooling on and off during tool switches
        No corresponding GCode exists as far as I know.
    """
    if tags is None:
        tags = []
    # Please note that these are the heatbreak cooling fans, not the object cooling
    return {"command": {"function": "toggle_fan",
                        "metadata": {},
                        "parameters": {"index": index, "value": value},
                        "tags": tags}}


def fan_duty(index: int, value: float, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """ Set object cooling fan speed (M106, M107) in Makerbot json format """
    if tags is None:
        tags = []
    # These are the object cooling fans
    return {"command": {"function": "fan_duty",
                        "metadata": {},
                        "parameters": {"index": index, "value": value},
                        "tags": tags}}


def delay(seconds: float, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    """ Pause (G4) in Makerbot json format """
    if tags is None:
        tags = []
    return {"command": {"function":
                            "delay", "metadata": {},
                        "parameters": {"seconds": seconds},
                        "tags": tags}}


def _incrementOrStartCount(metadata: Dict, key: str) -> None:
    if key in metadata:
        metadata[key] = metadata[key] + 1
    else:
        metadata[key] = 1


def convert(gcode: str) -> Tuple[str, Dict]:
    """
    The prime tower middle x,y position is used to heatup the print heads during a print head switch
    Convert a given gcode text string into:
     - a output command string in json or adjusted gcode (depending on Sketch or Method).
     - a meta data dictionary
     - a file name for the generated output commands
    """
    metadata = {}
    metadata["platform_temperature"] = 0  # FIXME! Always 0 for Methods. Those just have a build-volume temp.

    commands: List[Dict[str, Any]] = []
    section: List[Union[Dict[str, Any], str]] = []  # List of commands
    tool_nr = 0  # Current active toolhead 0 or 1
    layer_nr = 0
    section_nr = 1
    curr_low_pos = 10000
    curr_high_pos = -10000
    old_low_pos = 0.0
    old_high_pos = 0.0
    speed = 5.0  # mm/sec
    fan_on = [False, False]
    fan_speed = 1.0
    temperature = 0
    pos = zeros(4)  # x,y,z,e
    last_pos = zeros(4)  # x,y,z,e
    line_type = 'TRAVEL'
    volume = [0, 0]
    temperatures = [0, 0]
    materials = ["", ""]
    printheads = ["", ""]
    dual_extrusion = False
    bot = ""
    result = ""

    application = CuraApplication.getInstance()
    machine_manager = application.getMachineManager()
    global_stack = machine_manager.activeMachine

    prime_tower_x = global_stack.getProperty("prime_tower_position_x", "value")
    prime_tower_y = global_stack.getProperty("prime_tower_position_y", "value")
    prime_tower_size = global_stack.getProperty("prime_tower_size", "value")

    # Logger.log("d", f"Prime tower: ({prime_tower_x},{prime_tower_y}) and size {prime_tower_size}")

    prime_tower_x = prime_tower_x - prime_tower_size / 2  # we need the prime tower middle point
    prime_tower_y = prime_tower_y + prime_tower_size / 2  # see engine source code

    # Logger.log("i","Converting ufp to makerbot format")
    for line in gcode.splitlines():  # split gcode lines and loop through them
        _incrementOrStartCount(metadata, "total_commands")
        if line.startswith(';'):  # Line is a comment, extract info
            if line.startswith(";LAYER:"):  # Track the layer number
                _incrementOrStartCount(metadata, "num_z_layers")
                layer_nr = int(line.split(';LAYER:')[1].strip())
            elif line.startswith(";TYPE:"):  # Track the line type, = end of a layer section
                line_type = line[6:].strip()

                if curr_high_pos == -10000:  # keep track of z heights within this layer section
                    curr_low_pos = old_low_pos
                    curr_high_pos = old_high_pos
                old_low_pos = curr_low_pos
                old_high_pos = curr_high_pos

                section = add_section_json(section,
                                           tool_nr=tool_nr,
                                           section_nr=section_nr,
                                           low_pos=curr_low_pos,
                                           high_pos=curr_high_pos)
                commands.extend(section)
                section = []  # start new layer section
                section_nr += 1
                curr_low_pos = 10000
                curr_high_pos = -10000

            elif line.startswith(";TARGET_MACHINE.NAME:"):
                bot = line.replace(";TARGET_MACHINE.NAME:", "").strip()
                gcode_bot = "Sketch" in bot  # these machine read gcode
            elif line.startswith(";PRINT.TIME:"):
                duration = float(line.replace(";PRINT.TIME:", ""))
            elif line.startswith(";PRINT.SIZE.MIN.X:"):
                pass
            elif line.startswith(";PRINT.SIZE.MAX.X:"):
                pass
            elif line.startswith(";PRINT.SIZE.MIN.Y:"):
                pass
            elif line.startswith(";PRINT.SIZE.MAX.Y:"):
                pass
            elif line.startswith(";PRINT.SIZE.MIN.Z:"):
                pass
            elif line.startswith(";PRINT.SIZE.MAX.Z:"):
                pass
            elif line.startswith(";EXTRUDER_TRAIN.0.MATERIAL.VOLUME_USED:"):
                volume[0] = float(line.replace(";EXTRUDER_TRAIN.0.MATERIAL.VOLUME_USED:", ""))
            elif line.startswith(";EXTRUDER_TRAIN.1.MATERIAL.VOLUME_USED:"):
                volume[1] = float(line.replace(";EXTRUDER_TRAIN.1.MATERIAL.VOLUME_USED:", ""))
                if volume[1] > 0:
                    dual_extrusion = True
            elif line.startswith(";BUILD_PLATE.INITIAL_TEMPERATURE:"):
                # Build plate temperature (assumed for now, it seems that their files only set the chamber temperature)
                pass
            elif line.startswith(";BUILD_VOLUME.TEMPERATURE:"):
                pass
            elif line.startswith(";EXTRUDER_TRAIN.0.INITIAL_TEMPERATURE:"):
                temperatures[0] = int(line.replace(";EXTRUDER_TRAIN.0.INITIAL_TEMPERATURE:", ""))
            elif line.startswith(";EXTRUDER_TRAIN.1.INITIAL_TEMPERATURE:"):
                temperatures[1] = int(line.replace(";EXTRUDER_TRAIN.1.INITIAL_TEMPERATURE:", ""))
            elif line.startswith(";EXTRUDER_TRAIN.0.MATERIAL.GUID:"):
                materials[0] = material_lut.get(line.replace(";EXTRUDER_TRAIN.0.MATERIAL.GUID:", "").strip())
            elif line.startswith(";EXTRUDER_TRAIN.1.MATERIAL.GUID:"):
                materials[1] = material_lut.get(line.replace(";EXTRUDER_TRAIN.1.MATERIAL.GUID:", "").strip())
            elif line.startswith(";EXTRUDER_TRAIN.0.NOZZLE.NAME:"):
                ph = line.replace(";EXTRUDER_TRAIN.0.NOZZLE.NAME:", "").strip()
                if ph in printhead_lut:
                    printheads[0] = printhead_lut[ph]
            elif line.startswith(";EXTRUDER_TRAIN.1.NOZZLE.NAME:"):
                ph = line.replace(";EXTRUDER_TRAIN.1.NOZZLE.NAME:", "").strip()
                if ph in printhead_lut:
                    printheads[1] = printhead_lut[ph]

        elif line.startswith('G0 ') or line.startswith('G1 '):  # Move
            # Logger.log("i", line)
            pos, speed, a, b, tags = analyse_move(line, pos, speed, last_pos, tool_nr, layer_nr, line_type)
            if last_pos[2] != pos[2]:
                _incrementOrStartCount(metadata, "num_z_transitions")
            last_pos = pos.copy()
            curr_high_pos = max(curr_high_pos, pos[2])
            curr_low_pos = min(curr_low_pos, pos[2])
            section.append(move(x=pos[0], y=pos[1], z=pos[2], a=a, b=b, feedrate=speed, tags=tags))

        else:  # no comments and no move = other commands

            if line.startswith('G92 E0'):  # Reset extrusion channel
                pos[3] = 0.0
                last_pos[3] = 0.0

            elif line.startswith('T'):  # toolswitch. todo: check if this logic is OK
                """ Switch sequence seems to be:
                    Set soon to be deactivated print head to standby temperature
                    Object cooling to full power (100%) for this print head to prevent oozing
                    Set print temperature of soon to become active print head
                    z hop 0.4mm at 10mm/s
                    Move in x direction at 500mm/s to <unknown> x position
                    un z hop 0.4mm at 10mm/s
                    change tool head (I guess it now bumps the side wall) with wait for temperature position
                    Move to wait for temperature (prime tower middle) position with 500mm/s
                    Wait for temperature of new print core to have reached print temp.
                    Wait an extra 5 seconds
                    Toggle object cooling fans off for the deactivated print head
                    Toggle object cooling in for the activated print head
                    Set fan duty cycle back to normal value (thus not 100%)
                """
                _incrementOrStartCount(metadata, "num_tool_changes")
                index = int(line[1:].strip())
                if tool_nr != index:
                    tool_nr = index  # New active tool
                    old_active_tool_nr = (tool_nr + 1) % 2  # Tool to be deactiviated
                    # temperatures are already set by Cura before the print head switch

                    # set fan at full speed (cooling soon to be inactive head to prevent oozing)
                    section.append(fan_duty(index=old_active_tool_nr, value=1.0))
                    # zhop 0.4mm with 10mm/s
                    section.append(
                        move(x=last_pos[0], y=last_pos[1], z=last_pos[2] + 0.4, a=0, b=0, feedrate=10, tags=['Z hop']))
                    # move to side with 250mm/s
                    section.append(move(x=last_pos[0], y=last_pos[1], z=last_pos[2] + 0.4, a=0, b=0, feedrate=250,
                                        tags=["Quick Toggle"]))
                    # unhop -0.4mm with 10mm/s
                    # section.append(move(x=prime_tower_x, y=last_pos[1], z=last_pos[2], a=0, b=0, feedrate=10, tags=["Un Z hop"]))
                    # section.append(move(x=prime_tower_x, y=last_pos[1], z=last_pos[2], a=0, b=0, feedrate=250, tags=["Un Z hop"])) # set last speed to 250
                    # change tool and move to wait position (center of prime tower)
                    section.append(change_toolhead(index=index, x=prime_tower_x, y=prime_tower_y, tags=["Travel Move"]))
                    section.append(wait_for_temperature(index=tool_nr))
                    section.append(delay(5))
                    # Swap object cooling fan and set correct fan speed on new tool
                    if fan_on[
                        old_active_tool_nr]:  # Turn off the cold end cooling fan of the print head that will become active
                        fan_on[old_active_tool_nr] = False
                        section.append(toggle_fan(index=old_active_tool_nr, value=False))
                    if not fan_on[tool_nr]:
                        fan_on[tool_nr] = True
                        section.append(toggle_fan(index=tool_nr, value=True))
                    section.append(fan_duty(index=tool_nr, value=fan_speed))
                    # Move back to the edge of the prime tower
                    section.append(move(x=last_pos[0], y=last_pos[1], z=last_pos[2] + 0.4, a=0, b=0, feedrate=100,
                                        tags=['Wait for Temperature', "Travel Move"]))
                    section.append(move(x=last_pos[0], y=last_pos[1], z=last_pos[2], a=0, b=0, feedrate=10,
                                        tags=["Un Z hop"]))

            elif line.split(" ")[0] in ('M104', 'M109'):  # Set hot end temperature
                parts = line.split()
                if parts[1].startswith('T'):
                    index = int(parts[1][1:].strip())
                    temperature = int(float(parts[2][1:]))
                else:
                    index = tool_nr
                    temperature = int(float(parts[1][1:]))  # remove S
                section.append(set_toolhead_temperature(index=index, temperature=temperature))
                if line.startswith('M109'):  # Wait for temperature to be reached
                    section.append(wait_for_temperature(index=index))
                    # if fan_on[0]:  # Turn off the coldend cooling fans
                    #     fan_on[0] = False
                    #     section.append(toggle_fan(index=0, value=False))
                    # if fan_on[1]:
                    #     fan_on[1] = False
                    #     section.append(toggle_fan(index=1, value=False))

            elif line.startswith('M106'):  # Set object cooling fan speed
                parts = line.split()
                fan_speed = float(parts[1][1:]) / 255.0
                section.append(fan_duty(index=tool_nr, value=fan_speed))

            elif line.startswith('M107'):  # turn off fans
                section.append(fan_duty(index=0, value=0))
                section.append(fan_duty(index=1, value=0))

            elif line.startswith('G4'):  # dwell/delay
                seconds = float(line.split()[1][1:])
                section.append(delay(seconds=seconds))

    # Write last layer section and create the result string

    section = add_section_json(section,
                               tool_nr=tool_nr,
                               section_nr=section_nr,
                               low_pos=curr_low_pos,
                               high_pos=curr_high_pos)
    commands.extend(section)
    result = "[\n" + ",\n".join([json.dumps(command) for command in commands]) + "\n]"

    density = 1.2  # todo get from material profiles
    area = pi * (1.75 / 2) ** 2

    # Logger.log("i", "Converting mesh to makerbot format: done. Adding meta data")
    if "Method" not in bot:  # single print head bots, remove 2nd extruder metadata
        materials.pop()
        temperatures.pop()
        volume.pop()
        printheads.pop()
        printheads[0] = extruder_lut[bot]
    else:
        pass

    return result, metadata


def analyse_move(line: str, pos, speed, last_pos, tool_nr, layer_nr, line_type) -> Tuple[
    List[float], float, float, float, List[str]]:
    """ Analyse a G0 or G1 move and extract the X,Y,Z,E and speed and tag data from it
    """
    parts = line.split()
    for part in parts:
        segment = part[0]
        if segment == "X":
            pos[0] = float(part[1:])
        elif segment == "Y":
            pos[1] = float(part[1:])
        elif segment == "Z":
            pos[2] = float(part[1:])
        elif segment == "E":
            pos[3] = float(part[1:])
        elif segment == "F":
            speed = float(part[1:]) / 60  # From mm/min to mm/sec
    delta = pos - last_pos
    dist = norm(delta[:3])  # Segment length [mm]
    if tool_nr == 0:
        a, b = delta[3], 0
    else:
        a, b = 0, delta[3]

    tags = []
    t = max(dist / speed, abs(delta[3]) / speed)  # Time spend in this segment (acc./dec. neglected!) [sec]
    # NOTE: For future improvements we might want to use the Marlin planner as it is implemented in the GCodeAnalyzer:
    #       https://github.com/Ultimaker/GCodeAnalyzer/blob/main/GCodeAnalyzer/planner/marlin.py
    #       to determine the time; which would take into account acc./dec. and jerk.
    if isfinite(t) and t > 0.0:
        if delta[3] == 0.0 and dist > 0.0:
            tags.extend(tags_lut["TRAVEL"])  # TRAVEL move
        elif delta[3] < 0.0:
            tags.extend(tags_lut["RETRACT"])  # RETRACT move
        elif delta[3] > 0.0 and dist == 0.0:
            tags.extend(tags_lut["UNRETRACT"])  # UNRETRACT move
        else:
            tags.extend(tags_lut[line_type])
        if layer_nr < 0:
            tags.extend(['Raft'])
    return pos, speed, a, b, tags


def add_section_gcode(section: List[str], low_pos: float, high_pos: float, section_nr: int, result: str) -> str:
    """ Add a layer section to a gcode file (for Sketch machines)"""
    section.insert(0, "; Width          1;")
    section.insert(0, f"; Thickness      {high_pos - low_pos};")
    section.insert(0, f"; Upper Position {high_pos};")
    section.insert(0, f"; Lower Position {low_pos};")
    section.insert(0, f"; Material 0;")
    section.insert(0, f"; Layer Section {section_nr} ({section_nr});")  # TODO: Find out with these '()' numbers really mean, assume they maybe need to be unique.
    section.insert(0, "; Update Progress;")
    return result + '\n' + '\n'.join(section)


def add_section_json(section: List[Dict[str, Any]], tool_nr: int, section_nr: int,
                     low_pos: float, high_pos: float) -> Tuple[List[Dict[str, Any]], float, float]:
    """
    Add a layer section to json print file (Method and Replicator machines)
    Example for the json machines:
    "command": {"function": "comment", "metadata": {}, "parameters": {"comment": "Layer Section 11 (4)"}, "tags": []}
    "command": {"function": "comment", "metadata": {}, "parameters": {"comment": "Material 1"}, "tags": []}
    "command": {"function": "comment", "metadata": {}, "parameters": {"comment": "Lower Position  1"}, "tags": []}
    "command": {"function": "comment", "metadata": {}, "parameters": {"comment": "Upper Position  1.27"}, "tags": []}
    "command": {"function": "comment", "metadata": {}, "parameters": {"comment": "Thickness       0.27"}, "tags": []}
    "command": {"function": "comment", "metadata": {}, "parameters": {"comment": "Width           0.4"}, "tags": []}
    """
    section.insert(0, comment(f"Width          0.4"))
    section.insert(0, comment(f"Thickness      {high_pos - low_pos}"))
    section.insert(0, comment(f"Upper Position {high_pos}"))
    section.insert(0, comment(f"Lower Position {low_pos}"))  # Todo better fall back if position is unknown
    section.insert(0, comment(f"Material {tool_nr}"))
    section.insert(0, comment(f"Layer Section {section_nr} ({section_nr})"))  # TODO: Find out with these '()' numbers really mean, assume they maybe need to be unique.

    return section
