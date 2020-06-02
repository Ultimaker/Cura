#!/usr/bin/env python3
# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

import copy
import math
import os
import sys
from typing import Dict, List, Optional, Tuple


# ====================================
# Constants and Default Values
# ====================================
DEFAULT_BUFFER_FILLING_RATE_IN_C_PER_S = 50.0  # The buffer filling rate in #commands/s
DEFAULT_BUFFER_SIZE = 15  # The buffer size in #commands
MINIMUM_PLANNER_SPEED = 0.05

#Setting values for Ultimaker S5.
MACHINE_MAX_FEEDRATE_X = 300
MACHINE_MAX_FEEDRATE_Y = 300
MACHINE_MAX_FEEDRATE_Z = 40
MACHINE_MAX_FEEDRATE_E = 45
MACHINE_MAX_ACCELERATION_X = 9000
MACHINE_MAX_ACCELERATION_Y = 9000
MACHINE_MAX_ACCELERATION_Z = 100
MACHINE_MAX_ACCELERATION_E = 10000
MACHINE_MAX_JERK_XY = 20
MACHINE_MAX_JERK_Z = 0.4
MACHINE_MAX_JERK_E = 5
MACHINE_MINIMUM_FEEDRATE = 0.001
MACHINE_ACCELERATION = 3000


def get_code_and_num(gcode_line: str) -> Tuple[str, str]:
    """Gets the code and number from the given g-code line."""

    gcode_line = gcode_line.strip()
    cmd_code = gcode_line[0].upper()
    cmd_num = str(gcode_line[1:])
    return cmd_code, cmd_num


def get_value_dict(parts: List[str]) -> Dict[str, str]:
    """Fetches arguments such as X1 Y2 Z3 from the given part list and returns a dict"""

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
        distance += value ** 2
    distance = math.sqrt(distance)
    return distance


def calc_acceleration_distance(init_speed: float, target_speed: float, acceleration: float) -> float:
    """Given the initial speed, the target speed, and the acceleration

    calculate the distance that's neede for the acceleration to finish.
    """
    if acceleration == 0:
        return 0.0
    return (target_speed ** 2 - init_speed ** 2) / (2 * acceleration)


def calc_acceleration_time_from_distance(initial_feedrate: float, distance: float, acceleration: float) -> float:
    """Gives the time it needs to accelerate from an initial speed to reach a final distance."""

    discriminant = initial_feedrate ** 2 - 2 * acceleration * -distance
    #If the discriminant is negative, we're moving in the wrong direction.
    #Making the discriminant 0 then gives the extremum of the parabola instead of the intersection.
    discriminant = max(0, discriminant)
    return (-initial_feedrate + math.sqrt(discriminant)) / acceleration


def calc_intersection_distance(initial_feedrate: float, final_feedrate: float, acceleration: float, distance: float) -> float:
    """Calculates the point at which you must start braking.

    This gives the distance from the start of a line at which you must start
    decelerating (at a rate of `-acceleration`) if you started at speed
    `initial_feedrate` and accelerated until this point and want to end at the
    `final_feedrate` after a total travel of `distance`. This can be used to
    compute the intersection point between acceleration and deceleration in the
    cases where the trapezoid has no plateau (i.e. never reaches maximum speed).
    """

    if acceleration == 0:
        return 0
    return (2 * acceleration * distance - initial_feedrate * initial_feedrate + final_feedrate * final_feedrate) / (4 * acceleration)


def calc_max_allowable_speed(acceleration: float, target_velocity: float, distance: float) -> float:
    """Calculates the maximum speed that is allowed at this point when you must be
    able to reach target_velocity using the acceleration within the allotted
    distance.
    """

    return math.sqrt(target_velocity * target_velocity - 2 * acceleration * distance)


class Command:
    def __init__(self, cmd_str: str) -> None:
        self._cmd_str = cmd_str  # type: str

        self.estimated_exec_time = 0.0  # type: float

        self._cmd_process_function_map = {
            "G": self._handle_g,
            "M": self._handle_m,
            "T": self._handle_t,
        }

        self._is_comment = False  # type: bool
        self._is_empty = False  # type: bool

        #Fields taken from CuraEngine's implementation.
        self._recalculate = False
        self._accelerate_until = 0
        self._decelerate_after = 0
        self._initial_feedrate = 0
        self._final_feedrate = 0
        self._entry_speed = 0
        self._max_entry_speed =0
        self._nominal_length = False
        self._nominal_feedrate = 0
        self._max_travel = 0
        self._distance = 0
        self._acceleration = 0
        self._delta = [0, 0, 0]
        self._abs_delta = [0, 0, 0]

    def calculate_trapezoid(self, entry_factor, exit_factor):
        """Calculate the velocity-time trapezoid function for this move.

        Each move has a three-part function mapping time to velocity.
        """

        initial_feedrate = self._nominal_feedrate * entry_factor
        final_feedrate = self._nominal_feedrate * exit_factor

        #How far are we accelerating and how far are we decelerating?
        accelerate_distance = calc_acceleration_distance(initial_feedrate, self._nominal_feedrate, self._acceleration)
        decelerate_distance = calc_acceleration_distance(self._nominal_feedrate, final_feedrate, -self._acceleration)
        plateau_distance = self._distance - accelerate_distance - decelerate_distance #And how far in between at max speed?

        #Is the plateau negative size? That means no cruising, and we'll have to
        #use intersection_distance to calculate when to abort acceleration and
        #start braking in order to reach the final_rate exactly at the end of
        #this command.
        if plateau_distance < 0:
            accelerate_distance = calc_intersection_distance(initial_feedrate, final_feedrate, self._acceleration, self._distance)
            accelerate_distance = max(accelerate_distance, 0) #Due to rounding errors.
            accelerate_distance = min(accelerate_distance, self._distance)
            plateau_distance = 0

        self._accelerate_until = accelerate_distance
        self._decelerate_after = accelerate_distance + plateau_distance
        self._initial_feedrate = initial_feedrate
        self._final_feedrate = final_feedrate

    @property
    def is_command(self) -> bool:
        return not self._is_comment and not self._is_empty

    def __str__(self) -> str:
        if self._is_comment or self._is_empty:
            return self._cmd_str

        info = "t=%s" % (self.estimated_exec_time)

        return self._cmd_str.strip() + " ; --- " + info + os.linesep

    def parse(self) -> None:
        """Estimates the execution time of this command and calculates the state after this command is executed."""

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
        self.estimated_exec_time = 0.0

        # G10: Retract. Make this behave as if it's a retraction of 25mm.
        if cmd_num == 10:
            #TODO: If already retracted, this shouldn't add anything to the time.
            cmd_num = 1
            parts = ["G1", "E" + str(buf.current_position[3] - 25)]
        # G11: Unretract. Make this behave as if it's an unretraction of 25mm.
        elif cmd_num == 11:
            #TODO: If already unretracted, this shouldn't add anything to the time.
            cmd_num = 1
            parts = ["G1", "E" + str(buf.current_position[3] + 25)]

        # G0 and G1: Move
        if cmd_num in (0, 1):
            # Move
            if len(parts) > 0:
                value_dict = get_value_dict(parts[1:])

                new_position = copy.deepcopy(buf.current_position)
                new_position[0] = float(value_dict.get("X", new_position[0]))
                new_position[1] = float(value_dict.get("Y", new_position[1]))
                new_position[2] = float(value_dict.get("Z", new_position[2]))
                new_position[3] = float(value_dict.get("E", new_position[3]))
                buf.current_feedrate = float(value_dict.get("F", buf.current_feedrate * 60.0)) / 60.0
                if buf.current_feedrate < MACHINE_MINIMUM_FEEDRATE:
                    buf.current_feedrate = MACHINE_MINIMUM_FEEDRATE

                self._delta = [
                    new_position[0] - buf.current_position[0],
                    new_position[1] - buf.current_position[1],
                    new_position[2] - buf.current_position[2],
                    new_position[3] - buf.current_position[3]
                ]
                self._abs_delta = [abs(x) for x in self._delta]
                self._max_travel = max(self._abs_delta)
                if self._max_travel > 0:
                    self._nominal_feedrate = buf.current_feedrate
                    self._distance = math.sqrt(self._abs_delta[0] ** 2 + self._abs_delta[1] ** 2 + self._abs_delta[2] ** 2)
                    if self._distance == 0:
                        self._distance = self._abs_delta[3]

                    current_feedrate = [d * self._nominal_feedrate / self._distance for d in self._delta]
                    current_abs_feedrate = [abs(f) for f in current_feedrate]
                    feedrate_factor = min(1.0, MACHINE_MAX_FEEDRATE_X)
                    feedrate_factor = min(feedrate_factor, MACHINE_MAX_FEEDRATE_Y)
                    feedrate_factor = min(feedrate_factor, buf.max_z_feedrate)
                    feedrate_factor = min(feedrate_factor, MACHINE_MAX_FEEDRATE_E)
                    #TODO: XY_FREQUENCY_LIMIT

                    current_feedrate = [f * feedrate_factor for f in current_feedrate]
                    current_abs_feedrate = [f * feedrate_factor for f in current_abs_feedrate]
                    self._nominal_feedrate *= feedrate_factor

                    self._acceleration = MACHINE_ACCELERATION
                    max_accelerations = [MACHINE_MAX_ACCELERATION_X, MACHINE_MAX_ACCELERATION_Y, MACHINE_MAX_ACCELERATION_Z, MACHINE_MAX_ACCELERATION_E]
                    for n in range(len(max_accelerations)):
                        if self._acceleration * self._abs_delta[n] / self._distance > max_accelerations[n]:
                            self._acceleration = max_accelerations[n]

                    vmax_junction = MACHINE_MAX_JERK_XY / 2
                    vmax_junction_factor = 1.0
                    if current_abs_feedrate[2] > buf.max_z_jerk / 2:
                        vmax_junction = min(vmax_junction, buf.max_z_jerk)
                    if current_abs_feedrate[3] > buf.max_e_jerk / 2:
                        vmax_junction = min(vmax_junction, buf.max_e_jerk)
                    vmax_junction = min(vmax_junction, self._nominal_feedrate)
                    safe_speed = vmax_junction

                    if buf.previous_nominal_feedrate > 0.0001:
                        xy_jerk = math.sqrt((current_feedrate[0] - buf.previous_feedrate[0]) ** 2 + (current_feedrate[1] - buf.previous_feedrate[1]) ** 2)
                        vmax_junction = self._nominal_feedrate
                        if xy_jerk > MACHINE_MAX_JERK_XY:
                            vmax_junction_factor = MACHINE_MAX_JERK_XY / xy_jerk
                        if abs(current_feedrate[2] - buf.previous_feedrate[2]) > MACHINE_MAX_JERK_Z:
                            vmax_junction_factor = min(vmax_junction_factor, (MACHINE_MAX_JERK_Z / abs(current_feedrate[2] - buf.previous_feedrate[2])))
                        if abs(current_feedrate[3] - buf.previous_feedrate[3]) > MACHINE_MAX_JERK_E:
                            vmax_junction_factor = min(vmax_junction_factor, (MACHINE_MAX_JERK_E / abs(current_feedrate[3] - buf.previous_feedrate[3])))
                        vmax_junction = min(buf.previous_nominal_feedrate, vmax_junction * vmax_junction_factor) #Limit speed to max previous speed.

                    self._max_entry_speed = vmax_junction
                    v_allowable = calc_max_allowable_speed(-self._acceleration, MINIMUM_PLANNER_SPEED, self._distance)
                    self._entry_speed = min(vmax_junction, v_allowable)
                    self._nominal_length = self._nominal_feedrate <= v_allowable
                    self._recalculate = True

                    buf.previous_feedrate = current_feedrate
                    buf.previous_nominal_feedrate = self._nominal_feedrate
                    buf.current_position = new_position

                    self.calculate_trapezoid(self._entry_speed / self._nominal_feedrate, safe_speed / self._nominal_feedrate)

                    self.estimated_exec_time = -1 #Signal that we need to include this in our second pass.

        # G4: Dwell, pause the machine for a period of time.
        elif cmd_num == 4:
            # Pnnn is time to wait in milliseconds (P0 wait until all previous moves are finished)
            cmd, num = get_code_and_num(parts[1])
            num = float(num)
            if cmd == "P":
                if num > 0:
                    self.estimated_exec_time = num

    def _handle_m(self, cmd_num: int, parts: List[str]) -> None:
        self.estimated_exec_time = 0.0

        # M203: Set maximum feedrate. Only Z is supported. Assume 0 execution time.
        if cmd_num == 203:
            value_dict = get_value_dict(parts[1:])
            buf.max_z_feedrate = value_dict.get("Z", buf.max_z_feedrate)

        # M204: Set default acceleration. Assume 0 execution time.
        if cmd_num == 204:
            value_dict = get_value_dict(parts[1:])
            buf.acceleration = value_dict.get("S", buf.acceleration)

        # M205: Advanced settings, we only set jerks for Griffin. Assume 0 execution time.
        if cmd_num == 205:
            value_dict = get_value_dict(parts[1:])
            buf.max_xy_jerk = value_dict.get("XY", buf.max_xy_jerk)
            buf.max_z_jerk = value_dict.get("Z", buf.max_z_jerk)
            buf.max_e_jerk = value_dict.get("E", buf.max_e_jerk)

    def _handle_t(self, cmd_num: int, parts: List[str]) -> None:
        # Tn: Switching extruder. Assume 0 seconds. Actually more like 2.
        self.estimated_exec_time = 0.0


class CommandBuffer:
    def __init__(self, all_lines: List[str],
                 buffer_filling_rate: float = DEFAULT_BUFFER_FILLING_RATE_IN_C_PER_S,
                 buffer_size: int = DEFAULT_BUFFER_SIZE
                 ) -> None:
        self._all_lines = all_lines
        self._all_commands = list()

        self._buffer_filling_rate = buffer_filling_rate  # type: float
        self._buffer_size = buffer_size  # type: int

        self.acceleration = 3000
        self.current_position = [0, 0, 0, 0]
        self.current_feedrate = 0
        self.max_xy_jerk = MACHINE_MAX_JERK_XY
        self.max_z_jerk = MACHINE_MAX_JERK_Z
        self.max_e_jerk = MACHINE_MAX_JERK_E
        self.max_z_feedrate = MACHINE_MAX_FEEDRATE_Z

        # If the buffer can depletes less than this amount time, it can be filled up in time.
        lower_bound_buffer_depletion_time = self._buffer_size / self._buffer_filling_rate  # type: float

        self._detection_time_frame = lower_bound_buffer_depletion_time
        self._code_count_limit = self._buffer_size
        self.total_time = 0.0

        self.previous_feedrate = [0, 0, 0, 0]
        self.previous_nominal_feedrate = 0

        print("Command speed: %s" % buffer_filling_rate)
        print("Code Limit: %s" % self._code_count_limit)

        self._bad_frame_ranges = []

    def process(self) -> None:
        buf.total_time = 0.0
        cmd0_idx = 0
        total_frame_time = 0.0
        cmd_count = 0
        for idx, line in enumerate(self._all_lines):
            cmd = Command(line)
            cmd.parse()
            if not cmd.is_command:
                continue
            self._all_commands.append(cmd)

        #Second pass: Reverse kernel.
        kernel_commands = [None, None, None]
        for cmd in reversed(self._all_commands):
            if cmd.estimated_exec_time >= 0:
                continue #Not a movement command.
            kernel_commands[2] = kernel_commands[1]
            kernel_commands[1] = kernel_commands[0]
            kernel_commands[0] = cmd
            self.reverse_pass_kernel(kernel_commands[0], kernel_commands[1], kernel_commands[2])

        #Third pass: Forward kernel.
        kernel_commands = [None, None, None]
        for cmd in self._all_commands:
            if cmd.estimated_exec_time >= 0:
                continue #Not a movement command.
            kernel_commands[0] = kernel_commands[1]
            kernel_commands[1] = kernel_commands[2]
            kernel_commands[2] = cmd
            self.forward_pass_kernel(kernel_commands[0], kernel_commands[1], kernel_commands[2])
        self.forward_pass_kernel(kernel_commands[1], kernel_commands[2], None)

        #Fourth pass: Recalculate the commands that have _recalculate set.
        previous = None
        current = None
        for current in self._all_commands:
            if current.estimated_exec_time >= 0:
                current = None
                continue #Not a movement command.

            if previous:
                #Recalculate if current command entry or exit junction speed has changed.
                if previous._recalculate or current._recalculate:
                    #Note: Entry and exit factors always >0 by all previous logic operators.
                    previous.calculate_trapezoid(previous._entry_speed / previous._nominal_feedrate, current._entry_speed / previous._nominal_feedrate)
                    previous._recalculate = False

            previous = current
        if current is not None and current.estimated_exec_time >= 0:
            current.calculate_trapezoid(current._entry_speed / current._nominal_feedrate, MINIMUM_PLANNER_SPEED / current._nominal_feedrate)
            current._recalculate = False

        #Fifth pass: Compute time for movement commands.
        for cmd in self._all_commands:
            if cmd.estimated_exec_time >= 0:
                continue #Not a movement command.
            plateau_distance = cmd._decelerate_after - cmd._accelerate_until
            cmd.estimated_exec_time = calc_acceleration_time_from_distance(cmd._initial_feedrate, cmd._accelerate_until, cmd._acceleration)
            cmd.estimated_exec_time += plateau_distance / cmd._nominal_feedrate
            cmd.estimated_exec_time += calc_acceleration_time_from_distance(cmd._final_feedrate, (cmd._distance - cmd._decelerate_after), cmd._acceleration)

        for idx, cmd in enumerate(self._all_commands):
            cmd_count += 1
            if idx > cmd0_idx or idx == 0:
                buf.total_time += cmd.estimated_exec_time
                total_frame_time += cmd.estimated_exec_time

                if total_frame_time > 1:
                    # Find the next starting command which makes the total execution time of the frame to be less than
                    # 1 second.
                    cmd0_idx += 1
                    total_frame_time -= self._all_commands[cmd0_idx].estimated_exec_time
                    cmd_count -= 1
                    while total_frame_time > 1:
                        cmd0_idx += 1
                        total_frame_time -= self._all_commands[cmd0_idx].estimated_exec_time
                        cmd_count -= 1

                # If within the current time frame the code count exceeds the limit, record that.
                if total_frame_time <= self._detection_time_frame and cmd_count > self._code_count_limit:
                    need_to_append = True
                    if self._bad_frame_ranges:
                        last_item = self._bad_frame_ranges[-1]
                        if last_item["start_line"] == cmd0_idx:
                            last_item["end_line"] = idx
                            last_item["cmd_count"] = cmd_count
                            last_item["time"] = total_frame_time
                            need_to_append = False
                    if need_to_append:
                        self._bad_frame_ranges.append({"start_line": cmd0_idx,
                                                       "end_line": idx,
                                                       "cmd_count": cmd_count,
                                                       "time": total_frame_time})

    def reverse_pass_kernel(self, previous: Optional[Command], current: Optional[Command], next: Optional[Command]) -> None:
        if not current or not next:
            return

        #If entry speed is already at the maximum entry speed, no need to
        #recheck. The command is cruising. If not, the command is in state of
        #acceleration or deceleration. Reset entry speed to maximum and check
        #for maximum allowable speed reductions to ensure maximum possible
        #planned speed.
        if current._entry_speed != current._max_entry_speed:
            #If nominal length is true, max junction speed is guaranteed to be
            #reached. Only compute for max allowable speed if block is
            #decelerating and nominal length is false.
            if not current._nominal_length and current._max_entry_speed > next._max_entry_speed:
                current._entry_speed = min(current._max_entry_speed, calc_max_allowable_speed(-current._acceleration, next._entry_speed, current._distance))
            else:
                current._entry_speed = current._max_entry_speed
            current._recalculate = True

    def forward_pass_kernel(self, previous: Optional[Command], current: Optional[Command], next: Optional[Command]) -> None:
        if not previous:
            return

        #If the previous command is an acceleration command, but it is not long
        #enough to complete the full speed change within the command, we need to
        #adjust the entry speed accordingly. Entry speeds have already been
        #reset, maximised and reverse planned by the reverse planner. If nominal
        #length is set, max junction speed is guaranteed to be reached. No need
        #to recheck.
        if not previous._nominal_length:
            if previous._entry_speed < current._entry_speed:
                entry_speed = min(current._entry_speed, calc_max_allowable_speed(-previous._acceleration, previous._entry_speed, previous._distance))

                if current._entry_speed != entry_speed:
                    current._entry_speed = entry_speed
                    current._recalculate = True

    def to_file(self, file_name: str) -> None:
        all_lines = [str(c) for c in self._all_commands]
        with open(file_name, "w", encoding = "utf-8") as f:
            f.writelines(all_lines)
            f.write(";---TOTAL ESTIMATED TIME:" + str(self.total_time))

    def report(self) -> None:
        for item in self._bad_frame_ranges:
            print("Potential buffer underrun from line {start_line} to {end_line}, code count = {code_count}, in {time}s ({speed} cmd/s)".format(
                start_line = item["start_line"],
                end_line = item["end_line"],
                code_count = item["cmd_count"],
                time = round(item["time"], 4),
                speed = round(item["cmd_count"] / item["time"], 2)))
        print("Total predicted number of buffer underruns:", len(self._bad_frame_ranges))


if __name__ == "__main__":
    if len(sys.argv) < 2 or 3 < len(sys.argv):
        print("Usage: <input gcode> [output gcode]")
        sys.exit(1)
    in_filename = sys.argv[1]
    out_filename = None
    if len(sys.argv) == 3:
        out_filename = sys.argv[2]

    with open(in_filename, "r", encoding = "utf-8") as f:
        all_lines = f.readlines()

    buf = CommandBuffer(all_lines)
    buf.process()

    # Output annotated gcode is optional
    if out_filename is not None:
        buf.to_file(out_filename)

    buf.report()
