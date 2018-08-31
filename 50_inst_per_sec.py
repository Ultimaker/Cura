# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy
import math
import os
import sys
import random
from typing import Dict, List, Optional, Tuple


# ====================================
# Constants and Default Values
# ====================================
DEFAULT_BUFFER_FILLING_RATE_IN_C_PER_MS = 50.0 / 1000.0  # The buffer filling rate in #commands/ms
DEFAULT_BUFFER_SIZE = 15  # The buffer size in #commands

##  Gets the code and number from the given g-code line.
def get_code_and_num(gcode_line: str) -> Tuple[str, str]:
    gcode_line = gcode_line.strip()
    cmd_code = gcode_line[0].upper()
    cmd_num = str(gcode_line[1:])
    return cmd_code, cmd_num

##  Fetches arguments such as X1 Y2 Z3 from the given part list and returns a
#   dict.
def get_value_dict(parts: List[str]) -> Dict[str, str]:
    value_dict = {}
    for p in parts:
        p = p.strip()
        if not p:
            continue
        code, num = get_code_and_num(p)
        value_dict[code] = num
    return value_dict


# ============================
# Math Functions - Begin
# ============================

def calc_distance(pos1, pos2):
    delta = {k: pos1[k] - pos2[k] for k in pos1}
    distance = 0
    for value in delta.values():
        distance += value**2
    distance = math.sqrt(distance)
    return distance

##  Given the initial speed, the target speed, and the acceleration, calculate
#   the distance that's neede for the acceleration to finish.
def calc_acceleration_distance(init_speed: float, target_speed: float, acceleration: float) -> float:
    if acceleration == 0:
        return 0.0
    return (target_speed**2 - init_speed**2) / (2 * acceleration)


def calc_travel_time(p0, p1, init_speed: float, target_speed: float, acceleration: float) -> float:
    pass


class State:

    def __init__(self, previous_state: Optional["State"]) -> None:
        self.X = 0.0
        self.Y = 0.0
        self.Z = 0.0
        self.E = 0.0
        self.F = 0.0
        self.speed = {"X": 0.0,
                      "Y": 0.0,
                      "Z": 0.0,
                      }
        self.accelerations = {"XY": 0.0,
                              "Z": 0.0,
                              "S": 0.0,  # printing
                              "T": 0.0,  # travel
                              }
        self.jerks = {"X": 0.0,
                      "Y": 0.0,
                      "Z": 0.0,
                      }
        self.in_relative_positioning_mode = False  # type: bool
        self.in_relative_extrusion_mode = False  # type: bool

        if previous_state is not None:
            self.X = previous_state.X
            self.Y = previous_state.Y
            self.Z = previous_state.Z
            self.E = previous_state.E
            self.F = previous_state.F
            self.speed = copy.deepcopy(previous_state.speed)
            self.accelerations = copy.deepcopy(previous_state.accelerations)
            self.jerks = copy.deepcopy(previous_state.jerks)
            self.in_relative_positioning_mode = previous_state.in_relative_positioning_mode
            self.in_relative_extrusion_mode = previous_state.in_relative_extrusion_mode


class Command:

    def __init__(self, cmd_str: str, previous_state: "State") -> None:
        self._cmd_str = cmd_str  # type: str
        self._previous_state = previous_state  # type: State
        self._after_state = State(previous_state)  # type: State

        self._distance_in_mm = 0.0  # type float
        self._estimated_exec_time_in_ms = 0.0  # type: float

        self._cmd_process_function_map = {
            "G": self._handle_g,
            "M": self._handle_m,
            "T": self._handle_t,
        }

        self._is_comment = False  # type: bool
        self._is_empty = False  # type: bool

    def get_after_state(self) -> State:
        return self._after_state

    @property
    def is_command(self) -> bool:
        return not self._is_comment and not self._is_empty

    @property
    def estimated_exec_time_in_ms(self) -> float:
        return self._estimated_exec_time_in_ms

    def __str__(self) -> str:
        if self._is_comment or self._is_empty:
            return self._cmd_str

        distance_in_mm = round(self._distance_in_mm, 5)

        info = "d=%s f=%s t=%s" % (distance_in_mm, self._after_state.F, self._estimated_exec_time_in_ms)

        return self._cmd_str.strip() + " ; --- " + info + os.linesep

    def process(self) -> None:
        """
        Estimates the execution time of this command and calculates the state after this command is executed.
        """
        line = self._cmd_str.strip()
        if not line:
            self._is_empty = True
            return
        if line.startswith(";"):
            self._is_comment = True
            return

        # Remove comment
        line = line.split(";", 1)[0].strip()

        parts = line.split(" ")
        cmd_code, cmd_num = get_code_and_num(parts[0])
        cmd_num = int(cmd_num)

        func = self._cmd_process_function_map.get(cmd_code)
        if func is None:
            print("!!! no handle function for command type [%s]" % cmd_code)
            return
        func(cmd_num, parts)

    def _handle_g(self, cmd_num: int, parts: List[str]) -> None:
        estimated_exec_time_in_ms = 0.0

        # G0 and G1: Move
        if cmd_num in (0, 1):
            # Move
            distance = 0.0
            if len(parts) > 0:
                value_dict = get_value_dict(parts[1:])
                for key, value in value_dict.items():
                    setattr(self._after_state, key, float(value))

                current_position = {"X": self._previous_state.X,
                                    "Y": self._previous_state.Y,
                                    "Z": self._previous_state.Z,
                                    }
                new_position = copy.deepcopy(current_position)
                for key in new_position:
                    new_value = float(value_dict.get(key, new_position[key]))
                    new_position[key] = new_value

                distance = calc_distance(current_position, new_position)
                self._distance_in_mm = distance
            travel_time_in_ms = distance / (self._after_state.F / 60.0) * 1000.0

            estimated_exec_time_in_ms = travel_time_in_ms

            # TODO: take acceleration into account

        # G4: Dwell, pause the machine for a period of time. TODO
        if cmd_num == 4:
            # Pnnn is time to wait in milliseconds (P0 wait until all previous moves are finished)
            cmd, num = get_code_and_num(parts[1])
            num = float(num)
            if cmd == "P":
                if num > 0:
                    estimated_exec_time_in_ms = num

        # G10: Retract. Assume 0.3 seconds for short retractions and 0.5 seconds for long retractions.
        if cmd_num == 10:
            # S0 is short retract (default), S1 is long retract
            is_short_retract = True
            if len(parts) > 1:
                cmd, num = get_code_and_num(parts[1])
                if cmd == "S" and num == 1:
                    is_short_retract = False
            estimated_exec_time_in_ms = (0.3 if is_short_retract else 0.5) * 1000

        # G11: Unretract. Assume 0.5 seconds.
        if cmd_num == 11:
            estimated_exec_time_in_ms = 0.5 * 1000

        # G90: Set to absolute positioning. Assume 0 seconds.
        if cmd_num == 90:
            self._after_state.in_relative_positioning_mode = False
            estimated_exec_time_in_ms = 0.0

        # G91: Set to relative positioning. Assume 0 seconds.
        if cmd_num == 91:
            self._after_state.in_relative_positioning_mode = True
            estimated_exec_time_in_ms = 0.0

        # G92: Set position. Assume 0 seconds.
        if cmd_num == 92:
            # TODO: check
            value_dict = get_value_dict(parts[1:])
            for key, value in value_dict.items():
                setattr(self._previous_state, key, value)

        # G280: Prime. Assume 10 seconds for using blob and 5 seconds for no blob.
        if cmd_num == 280:
            use_blob = True
            if len(parts) > 1:
                cmd, num = get_code_and_num(parts[1])
                if cmd == "S" and num == 1:
                    use_blob = False
            estimated_exec_time_in_ms = (10.0 if use_blob else 5.0) * 1000

        # Update estimated execution time
        self._estimated_exec_time_in_ms = round(estimated_exec_time_in_ms, 5)

    def _handle_m(self, cmd_num: int, parts: List[str]) -> None:
        estimated_exec_time_in_ms = 0.0

        # M82: Set extruder to absolute mode. Assume 0 execution time.
        if cmd_num == 82:
            self._after_state.in_relative_extrusion_mode = False
            estimated_exec_time_in_ms = 0.0

        # M83: Set extruder to relative mode. Assume 0 execution time.
        if cmd_num == 83:
            self._after_state.in_relative_extrusion_mode = True
            estimated_exec_time_in_ms = 0.0

        # M104: Set extruder temperature (no wait). Assume 0 execution time.
        if cmd_num == 104:
            estimated_exec_time_in_ms = 0.0

        # M106: Set fan speed. Assume 0 execution time.
        if cmd_num == 106:
            estimated_exec_time_in_ms = 0.0

        # M107: Turn fan off. Assume 0 execution time.
        if cmd_num == 107:
            estimated_exec_time_in_ms = 0.0

        # M109: Set extruder temperature (wait). Uniformly random time between 30 - 90 seconds.
        if cmd_num == 109:
            estimated_exec_time_in_ms = random.uniform(30, 90) * 1000  # TODO: Check

        # M140: Set bed temperature (no wait). Assume 0 execution time.
        if cmd_num == 140:
            estimated_exec_time_in_ms = 0.0

        # M204: Set default acceleration. Assume 0 execution time.
        if cmd_num == 204:
            value_dict = get_value_dict(parts[1:])
            for key, value in value_dict.items():
                self._after_state.accelerations[key] = float(value)
            estimated_exec_time_in_ms = 0.0

        # M205: Advanced settings, we only set jerks for Griffin. Assume 0 execution time.
        if cmd_num == 205:
            value_dict = get_value_dict(parts[1:])
            for key, value in value_dict.items():
                self._after_state.jerks[key] = float(value)
            estimated_exec_time_in_ms = 0.0

        self._estimated_exec_time_in_ms = estimated_exec_time_in_ms

    def _handle_t(self, cmd_num: int, parts: List[str]) -> None:
        # Tn: Switching extruder. Assume 2 seconds.
        estimated_exec_time_in_ms = 2.0

        self._estimated_exec_time_in_ms = estimated_exec_time_in_ms


class CommandBuffer:
    def __init__(self, all_lines: List[str],
                 buffer_filling_rate: float = DEFAULT_BUFFER_FILLING_RATE_IN_C_PER_MS,
                 buffer_size: int = DEFAULT_BUFFER_SIZE
                 ) -> None:
        self._all_lines = all_lines
        self._all_commands = list()

        self._buffer_filling_rate = buffer_filling_rate  # type: float
        self._buffer_size = buffer_size  # type: int

        # If the buffer can depletes less than this amount time, it can be filled up in time.
        lower_bound_buffer_depletion_time = self._buffer_size / self._buffer_filling_rate  # type: float

        self._detection_time_frame = lower_bound_buffer_depletion_time
        self._code_count_limit = self._buffer_size
        print("Time Frame: %s" % self._detection_time_frame)
        print("Code Limit: %s" % self._code_count_limit)

        self._bad_frame_ranges = []

    def process(self) -> None:
        previous_state = None
        cmd0_idx = 0
        total_frame_time_in_ms = 0.0
        cmd_count = 0
        for idx, line in enumerate(self._all_lines):
            cmd = Command(line, previous_state)
            cmd.process()
            self._all_commands.append(cmd)
            previous_state = cmd.get_after_state()

            if not cmd.is_command:
                continue

            cmd_count += 1
            if idx > cmd0_idx or idx == 0:
                total_frame_time_in_ms += cmd.estimated_exec_time_in_ms

                if total_frame_time_in_ms > 1000.0:
                    # Find the next starting command which makes the total execution time of the frame to be less than
                    # 1 second.
                    cmd0_idx += 1
                    total_frame_time_in_ms -= self._all_commands[cmd0_idx].estimated_exec_time_in_ms
                    cmd_count -= 1
                    while total_frame_time_in_ms > 1000.0:
                        cmd0_idx += 1
                        total_frame_time_in_ms -= self._all_commands[cmd0_idx].estimated_exec_time_in_ms
                        cmd_count -= 1

                # If within the current time frame the code count exceeds the limit, record that.
                if total_frame_time_in_ms <= self._detection_time_frame and cmd_count > self._code_count_limit:
                    need_to_append = True
                    if self._bad_frame_ranges:
                        last_item = self._bad_frame_ranges[-1]
                        if last_item["start_line"] == cmd0_idx:
                            last_item["end_line"] = idx
                            last_item["cmd_count"] = cmd_count
                            last_item["time_in_ms"] = total_frame_time_in_ms
                            need_to_append = False
                    if need_to_append:
                        self._bad_frame_ranges.append({"start_line": cmd0_idx,
                                                       "end_line": idx,
                                                       "cmd_count": cmd_count,
                                                       "time_in_ms": total_frame_time_in_ms})

    def to_file(self, file_name: str) -> None:
        all_lines = [str(c) for c in self._all_commands]
        with open(file_name, "w", encoding = "utf-8") as f:
            f.writelines(all_lines)

    def report(self) -> None:
        for item in self._bad_frame_ranges:
            print("!!!!!  potential bad frame from line %s to %s, code count = %s, in %s ms" % (
                item["start_line"], item["end_line"], item["cmd_count"], round(item["time_in_ms"], 4)))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: <input gcode> <output gcode>")
        sys.exit(1)
    in_filename = sys.argv[1]
    out_filename = sys.argv[2]

    with open(in_filename, "r", encoding = "utf-8") as f:
        all_lines = f.readlines()

    buf = CommandBuffer(all_lines)
    buf.process()
    buf.to_file(out_filename)
    buf.report()
