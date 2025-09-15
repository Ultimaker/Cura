"""
Copyright (c) 2025 GregValiant (Greg Foresi)

 When Annealing:
    The user may elect to hold the build plate at a temperature for a period of time.  When the hold expires, the 'Timed Cooldown' will begin.
    If there is no 'Hold Time' then the 'Annealing' cooldown will begin when the print ends.  In 'Annealing' the bed temperature drops in 3° increments across the time span.
    G4 commands are used for the cooldown steps.
    If there is a 'Heated Chamber' then the chamber will start to cool when the bed temperature reaches the chamber temperature.

 When drying filament:
    The bed must be empty because the printer will auto-home before raising the Z to 'machine_height minus 20mm' and then park the head in the XY.
    The bed will heat up to the set point.
    G4 commands are used to keep the machine from turning the bed off until the Drying Time has expired.
 If you happen to have an enclosure with a fan, the fan can be set up to run during the drying or annealing.

 NOTE:  This script uses the G4 Dwell command as a timer.  It cannot be canceled from the LCD.  If you wish to 'escape' from G4 you might have to cancel the print from the LCD or cycle the printer on and off to reset.
"""

from UM.Application import Application
from ..Script import Script
from UM.Message import Message

class AnnealingOrDrying(Script):

    def initialize(self) -> None:
        super().initialize()
        # Get the Bed Temperature from Cura
        self.global_stack = Application.getInstance().getGlobalContainerStack()
        bed_temp_during_print = str(self.global_stack.getProperty("material_bed_temperature", "value"))
        self._instance.setProperty("startout_temp", "value", bed_temp_during_print)
        # Get the Build Volume temperature if there is one
        heated_build_volume = bool(self.global_stack.getProperty("machine_heated_build_volume", "value"))
        chamber_fan_nr = self.global_stack.getProperty("build_volume_fan_nr", "value")
        extruder_count = self.global_stack.getProperty("machine_extruder_count", "value")
        if heated_build_volume:
            chamber_temp = self.global_stack.getProperty("build_volume_temperature", "value")
            self._instance.setProperty("has_build_volume_heater", "value", heated_build_volume)
            self._instance.setProperty("build_volume_temp", "value", chamber_temp)
        try:
            if chamber_fan_nr > 0:
                self._instance.setProperty("enable_chamber_fan_setting", "value", True)
        except:
            pass

    def getSettingDataString(self):
        return """{
            "name": "Annealing CoolDown or Filament Drying",
            "key": "AnnealingOrDrying",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "enable_script":
                {
                    "label": "Enable the Script",
                    "description": "If it isn't enabled it doesn't run.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": true
                },
                "cycle_type":
                {
                    "label": "Anneal Print or Dry Filament",
                    "description": "Whether to Anneal the Print (by keeping the bed hot for a period of time), or to use the bed as a Filament Dryer.  If drying; you will still need to slice a model, but it will not print. The gcode will consist only of a short script to heat the bed, wait for a while, then turn the bed off.  The 'Z' will move to the max height and XY park position so the filament can be covered. The 'Hold Time', 'Bed Start Temp' and (if applicable) the 'Chamber Temp' come from these settings rather than from the Cura settings.  When annealing; the Timed Cooldown will commence when the print ends.",
                    "type": "enum",
                    "options":
                    {
                        "anneal_cycle": "Anneal Print",
                        "dry_cycle": "Dry Filament"
                    },
                    "default_value": "anneal_cycle",
                    "enabled": true,
                    "enabled": "enable_script"
                },
                "heating_zone_selection":
                {
                    "label": "Hold the Temp for the:",
                    "description": "Select the 'Bed' for just the bed, or 'Bed and Chamber' if you want to include your 'Heated Build Volume'.",
                    "type": "enum",
                    "options":
                    {
                        "bed_only": "Bed",
                        "bed_chamber": "Bed and Chamber"
                    },
                    "default_value": "bed_only",
                    "enabled": "enable_script"
                },
                "wait_time":
                {
                    "label": "Hold Time at Temp(s)",
                    "description": "Hold the bed temp at the 'Bed Start Out Temperature' for this amount of time (in decimal hours).  When this time expires then the Annealing cool down will start.  This is also the 'Drying Time' used when 'Drying Filament'.",
                    "type": "float",
                    "default_value": 0.0,
                    "unit": "Decimal Hrs ",
                    "enabled": "enable_script and cycle_type == 'anneal_cycle'"
                },
                "dry_time":
                {
                    "label": "Drying Time",
                    "description": "Hold the bed temp at the 'Bed Start Out Temperature' for this amount of time (in decimal hours).  When this time expires the bed will shut off.",
                    "type": "float",
                    "default_value": 4.0,
                    "unit": "Decimal Hrs ",
                    "enabled": "enable_script and cycle_type == 'dry_cycle'"
                },
                "pause_cmd":
                {
                    "label": "Pause Cmd for Auto-Home",
                    "description": "Not required when you are paying attention and the bed is empty; ELSE; Enter the pause command to use prior to the Auto-Home command.  The pause insures that the user IS paying attention and clears the build plate for Auto-Home.  If you leave the box empty then there won't be a pause.",
                    "type": "str",
                    "default_value": "",
                    "enabled": "enable_script and cycle_type == 'dry_cycle'"
                },
                "startout_temp":
                {
                    "label": "Bed Start Out Temperature:",
                    "description": "Enter the temperature to start at.  This is typically the bed temperature during the print but can be changed here.  This is also the temperature used when drying filament.",
                    "type": "int",
                    "value": 30,
                    "unit": "Degrees ",
                    "minimum_value": 30,
                    "maximum_value": 110,
                    "maximum_value_warning": 100,
                    "enabled": "enable_script"
                },
                "lowest_temp":
                {
                    "label": "Shut-Off Temp:",
                    "description": "Enter the lowest temperature to control the cool down.  This is the shut-off temperature for the build plate and (when applicable) the Heated Chamber.  The minimum value is 30",
                    "type": "int",
                    "default_value": 30,
                    "unit": "Degrees ",
                    "minimum_value": 30,
                    "enabled": "enable_script and cycle_type == 'anneal_cycle'"
                },
                "build_volume_temp":
                {
                    "label": "Build Volume Temperature:",
                    "description": "Enter the temperature for the Build Volume (Heated Chamber).  This is typically the temperature during the print but can be changed here.",
                    "type": "int",
                    "value": 24,
                    "unit": "Degrees ",
                    "minimum_value": 0,
                    "maximum_value": 90,
                    "maximum_value_warning": 75,
                    "enabled": "enable_script and has_build_volume_heater and heating_zone_selection == 'bed_chamber'"
                },
                "enable_chamber_fan_setting":
                {
                    "label": "Hidden Setting",
                    "description": "Enables chamber fan and speed.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                },
                "chamber_fan_speed":
                {
                    "label": "Chamber Fan Speed",
                    "description": "Set to % fan speed.  Set to 0 to turn it off.",
                    "type": "int",
                    "default_value": 0,
                    "minimum_value": 0,
                    "maximum_value": 100,
                    "unit": "% ",
                    "enabled": "enable_script and enable_chamber_fan_setting"
                },
                "time_span":
                {
                    "label": "Cool Down Time Span:",
                    "description": "The total amount of time (in decimal hours) to control the cool down.  The build plate temperature will be dropped in 3° increments across this time span.  'Cool Down Time' starts at the end of the 'Hold Time' if you entered one.",
                    "type": "float",
                    "default_value": 1.0,
                    "unit": "Decimal Hrs ",
                    "minimum_value_warning": 0.25,
                    "enabled": "enable_script and cycle_type == 'anneal_cycle'"
                },
                "park_head":
                {
                    "label": "Park at MaxX and MaxY",
                    "description": "When unchecked, the park position is X0 Y0.  Enable this setting to move the nozzle to the Max X and Max Y to allow access to the print.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_script and cycle_type == 'anneal_cycle'"
                },
                "park_max_z":
                {
                    "label": "Move to MaxZ",
                    "description": "Enable this setting to move the nozzle to 'Machine_Height - 20' to allow the print to be covered.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_script and cycle_type == 'anneal_cycle'"
                },
                "beep_when_done":
                {
                    "label": "Beep when done",
                    "description": "Add an annoying noise when the Cool Down completes.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "enable_script"
                },
                "beep_duration":
                {
                    "label": "Beep Duration",
                    "description": "The length of the buzzer sound.  Units are in milliseconds so 1000ms = 1 second.",
                    "type": "int",
                    "unit": "milliseconds ",
                    "default_value": 1000,
                    "enabled": "beep_when_done and enable_script"
                },
                "add_messages":
                {
                    "label": "Include M117 and M118 messages",
                    "description": "Add messages to the LCD and any print server.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": "enable_script"
                },
                "has_build_volume_heater":
                {
                    "label": "Hidden setting",
                    "description": "Hidden.  This setting enables the build volume settings.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": false
                }
            }
        }"""

    def execute(self, data):
        # Exit if there is no heated bed.
        if not bool(self.global_stack.getProperty("machine_heated_bed", "value")):
            Message(title = "[Anneal or Dry Filament]", text = "The script did not run because Heated Bed is disabled in Machine Settings.").show()
            return data
        # Enter a message in the gcode if the script is not enabled.
        if not bool(self.getSettingValueByKey("enable_script")):
            data[0] += ";    [Anneal or Dry Filament] was not enabled\n"
            return data
        lowest_temp = int(self.getSettingValueByKey("lowest_temp"))

        # If the shutoff temp is under 30° then exit as a safety precaution so the bed doesn't stay on.
        if lowest_temp < 30:
            data[0] += ";  Anneal or Dry Filament did not run.  Shutoff Temp < 30\n"
            Message(title = "[Anneal or Dry Filament]", text = "The script did not run because the Shutoff Temp is less than 30°.").show()
            return data
        extruders = self.global_stack.extruderList
        bed_temperature = int(self.getSettingValueByKey("startout_temp"))
        heated_chamber = bool(self.global_stack.getProperty("machine_heated_build_volume", "value"))
        heating_zone = self.getSettingValueByKey("heating_zone_selection")

        # Get the heated chamber temperature or set to 0 if no chamber
        if heated_chamber:
            chamber_temp = str(self.getSettingValueByKey("build_volume_temp"))
        else:
            heating_zone = "bed_only"
            chamber_temp = "0"

        # Beep line
        if bool(self.getSettingValueByKey("beep_when_done")):
            beep_duration = self.getSettingValueByKey("beep_duration")
            self.beep_string = f"M300 S440 P{beep_duration} ; Beep\n"
        else:
            self.beep_string = ""

        # For compatibility with earlier Cura versions
        if self.global_stack.getProperty("build_volume_fan_nr", "value") is not None:
            has_bv_fan = bool(self.global_stack.getProperty("build_volume_fan_nr", "value"))
            bv_fan_nr = int(self.global_stack.getProperty("build_volume_fan_nr", "value"))
            if bv_fan_nr > 0:
                speed_bv_fan = int(self.getSettingValueByKey("chamber_fan_speed"))
            else:
                speed_bv_fan = 0

            if bool(extruders[0].getProperty("machine_scale_fan_speed_zero_to_one", "value")) and has_bv_fan:
                speed_bv_fan = round(speed_bv_fan * 0.01)
            else:
                speed_bv_fan = round(speed_bv_fan * 2.55)

            if has_bv_fan and speed_bv_fan > 0:
                self.bv_fan_on_str = f"M106 S{speed_bv_fan} P{bv_fan_nr} ; Build Chamber Fan On\n"
                self.bv_fan_off_str = f"M106 S0 P{bv_fan_nr} ; Build Chamber Fan Off\n"
            else:
                self.bv_fan_on_str = ""
                self.bv_fan_off_str = ""
        else:
            has_bv_fan = False
            bv_fan_nr = 0
            speed_bv_fan = 0
            self.bv_fan_on_str = ""
            self.bv_fan_off_str = ""

        # Park Head
        max_y = str(self.global_stack.getProperty("machine_depth", "value"))
        max_x = str(self.global_stack.getProperty("machine_width", "value"))

        # Max_z is limited to 'machine_height - 20' just so the print head doesn't smack into anything.
        max_z = str(int(self.global_stack.getProperty("machine_height", "value")) - 20)
        speed_travel = str(round(extruders[0].getProperty("speed_travel", "value")*60))
        park_xy = bool(self.getSettingValueByKey("park_head"))
        park_z = bool(self.getSettingValueByKey("park_max_z"))
        cycle_type = self.getSettingValueByKey("cycle_type")
        add_messages = bool(self.getSettingValueByKey("add_messages"))

        if cycle_type == "anneal_cycle":
            data = self._anneal_print(add_messages, data, bed_temperature, chamber_temp, heated_chamber, heating_zone, lowest_temp, max_x, max_y, max_z, park_xy, park_z, speed_travel)
        elif cycle_type == "dry_cycle":
            data = self._dry_filament_only(data, bed_temperature, chamber_temp, heated_chamber, heating_zone, max_y, max_z, speed_travel)
        
        return data

    def _anneal_print(
            self,
            add_messages: bool,
            anneal_data: str,
            bed_temperature: int,
            chamber_temp: str,
            heated_chamber: bool,
            heating_zone: str,
            lowest_temp: int,
            max_x: str,
            max_y: str,
            max_z: str,
            park_xy: bool,
            park_z: bool,
            speed_travel: str) -> str:
        """
        The procedure disables the M140 (and M141) lines at the end of the print, and adds additional bed (and chamber) temperature commands to the end of the G-Code file.
        The bed is allowed to cool down over a period of time.
                
        :param add_messages: Whether to include M117 and M118 messages for LCD and print server
        :param anneal_data: The G-code data to be modified with annealing commands
        :param bed_temperature: Starting bed temperature in degrees Celsius
        :param chamber_temp: Chamber/build volume temperature in degrees Celsius as string
        :param heated_chamber: Whether the printer has a heated build volume/chamber
        :param heating_zone: Zone selection - "bed_only" or "bed_chamber"
        :param lowest_temp: Final shutdown temperature in degrees Celsius
        :param max_x: Maximum X axis position for parking as string
        :param max_y: Maximum Y axis position for parking as string
        :param max_z: Maximum Z axis position (machine height - 20mm) as string
        :param park_xy: Whether to park the print head at max X and Y positions
        :param park_z: Whether to raise Z to maximum safe height
        :param speed_travel: Travel speed for positioning moves in mm/min as string
        :return: Modified G-code data with annealing cooldown sequence
        """
        # Put the head parking string together
        bed_temp_during_print = int(self.global_stack.getProperty("material_bed_temperature", "value"))
        time_minutes = 1
        time_span = int(float(self.getSettingValueByKey("time_span")) * 3600)
        park_string = ""
        if park_xy:
                park_string += f"G0 F{speed_travel} X{max_x} Y{max_y} ; Park XY\n"
        if park_z:
                park_string += f"G0 Z{max_z} ; Raise Z to 'ZMax - 20'\n"
        if not park_xy and not park_z:
                park_string += f"G91 ; Relative movement\nG0 F{speed_travel} Z5 ; Raise Z\nG90 ; Absolute movement\nG0 X0 Y0 ; Park\n"
        park_string += "M84 X Y E ; Disable steppers except Z\n"

        # Calculate the temperature differential
        hysteresis = bed_temperature - lowest_temp

        # Exit if the bed temp is below the shutoff temp
        if hysteresis <= 0:
            anneal_data[0] += ";  Anneal or Dry Filament did not run.  Bed Temp < Shutoff Temp\n"
            Message(title = "Anneal or Dry Filament", text = "Did not run because the Bed Temp < Shutoff Temp.").show()
            return anneal_data

        # Drop the bed temperature in 3° increments.
        num_steps = int(hysteresis / 3)
        step_index = 2
        deg_per_step = int(hysteresis / num_steps)
        time_per_step = int(time_span / num_steps)
        step_down = bed_temperature
        wait_time = int(float(self.getSettingValueByKey("wait_time")) * 3600)

        # Put the first lines of the anneal string together
        anneal_string = ";\n;TYPE:CUSTOM ---------------- Anneal Print\n"
        if bed_temperature == bed_temp_during_print:
            anneal_string += self.beep_string
        if add_messages:
            anneal_string += "M117 Cool Down for " + str(round((wait_time + time_span)/3600,2)) + "hr\n"
            anneal_string += "M118 Cool Down for " + str(round((wait_time + time_span)/3600,2)) + "hr\n"
        anneal_string += self.bv_fan_on_str
        if wait_time > 0:
            # Add the parking string BEFORE the M190
            anneal_string += park_string
            if heating_zone == "bed_only":
                anneal_string += f"M190 S{bed_temperature} ; Set the bed temp\n{self.beep_string}"
            if heating_zone == "bed_chamber":
                anneal_string += f"M190 S{bed_temperature} ; Set the bed temp\nM141 S{chamber_temp} ; Set the chamber temp\n{self.beep_string}"
            anneal_string += f"G4 S{wait_time} ; Hold for {round(wait_time / 3600,2)} hrs\n"
        else:
            # Add the parking string AFTER the M140
            anneal_string += f"M140 S{step_down} ; Set bed temp\n"
            anneal_string += park_string
            anneal_string += f"G4 S{time_per_step} ; wait time in seconds\n"

        step_down -= deg_per_step
        time_remaining = round(time_span/3600,2)

        # Step the bed/chamber temps down and add each step to the anneal string.  The chamber remains at it's temperature until the bed gets down to that temperature.
        for num in range(bed_temperature, lowest_temp, -3):
            anneal_string += f"M140 S{step_down} ; Step down bed\n"
            if heating_zone == "bed_chamber" and int(step_down) < int(chamber_temp):
                anneal_string += f"M141 S{step_down} ; Step down chamber\n"
            anneal_string += f"G4 S{time_per_step} ; Wait\n"
            if time_remaining >= 1.00:
                if add_messages:
                    anneal_string += f"M117 CoolDown - {round(time_remaining,1)}hr\n"
                    anneal_string += f"M118 CoolDown - {round(time_remaining,1)}hr\n"
            elif time_minutes > 0:
                time_minutes = round(time_remaining * 60,1)
                if add_messages:
                    anneal_string += f"M117 CoolDown - {time_minutes}min\n"
                    anneal_string += f"M118 CoolDown - {time_minutes}min\n"
            time_remaining = round((time_span-(step_index*time_per_step))/3600,2)
            step_down -= deg_per_step
            step_index += 1
            if step_down <= lowest_temp:
                break

        # Close out the anneal string
        anneal_string += "M140 S0 ; Shut off the bed heater" + "\n"
        if heating_zone == "bed_chamber":
            anneal_string += "M141 S0 ; Shut off the chamber heater\n"
        anneal_string += self.bv_fan_off_str
        anneal_string += self.beep_string
        if add_messages:
            anneal_string += "M117 CoolDown Complete\n"
            anneal_string += "M118 CoolDown Complete\n"
        anneal_string += ";TYPE:CUSTOM ---------------- End of Anneal\n;"

        # Format the inserted lines.
        anneal_lines = anneal_string.split("\n")
        for index, line in enumerate(anneal_lines):
            if not line.startswith(";") and ";" in line:
                front_txt = anneal_lines[index].split(";")[0]
                back_txt = anneal_lines[index].split(";")[1]
                anneal_lines[index] = front_txt + str(" " * (30 - len(front_txt))) +";" +  back_txt
        anneal_string = "\n".join(anneal_lines) + "\n"

        end_gcode = anneal_data[-1]
        end_lines = end_gcode.split("\n")

        # Comment out the existing M140 S0 lines in the ending gcode.
        for num in range(len(end_lines)-1,-1,-1):
            if end_lines[num].startswith("M140 S0"):
                end_lines[num] = ";M140 S0 ; Shutoff Overide - Anneal or Dry Filament"
                anneal_data[-1] = "\n".join(end_lines)

        # If there is a Heated Chamber and it's included then comment out the M141 S0 line
        if heating_zone == "bed_chamber" and heated_chamber:
            for num in range(0,len(end_lines)-1):
                if end_lines[num].startswith("M141 S0"):
                    end_lines[num] = ";M141 S0 ; Shutoff Overide - Anneal or Dry Filament"
                    anneal_data[-1] = "\n".join(end_lines)

        # If park head is enabled then dont let the steppers disable until the head is parked
        disable_string = ""
        for num in range(0,len(end_lines)-1):
            if end_lines[num][:3] in ("M84", "M18"):
                disable_string = end_lines[num] + "\n"
                stepper_timeout = int(wait_time + time_span)
                if stepper_timeout > 14400: stepper_timeout = 14400
                end_lines[num] = ";" + end_lines[num] + " ; Overide - Anneal or Dry Filament"
                end_lines.insert(num, "M84 S" + str(stepper_timeout) + " ; Increase stepper timeout - Anneal or Dry Filament")
                anneal_data[-1] = "\n".join(end_lines)
                break

        # The Anneal string is the new end of the gcode so move the 'End of Gcode' comment line in case there are other scripts running
        anneal_data[-1] = anneal_data[-1].replace(";End of Gcode", anneal_string + disable_string + ";End of Gcode")
        return anneal_data

    def _dry_filament_only(
            self,
            bed_temperature: int,
            chamber_temp: int,
            drydata: str,
            heated_chamber: bool,
            heating_zone: str,
            max_y: str,
            max_z: str,
            speed_travel: str) -> str:
        """
        This procedure turns the bed on, homes the printer, parks the head.  After the time period the bed is turned off.
        There is no actual print in the generated gcode, just a couple of moves to get the nozzle out of the way, and the bed heat (and possibly chamber heat) control.
        It allows a user to use the bed to warm up and hopefully dry a filament roll.
                
        :param bed_temperature: Bed temperature for drying in degrees Celsius
        :param chamber_temp: Chamber/build volume temperature for drying in degrees Celsius
        :param drydata: The G-code data to be replaced with filament drying commands
        :param heated_chamber: Whether the printer has a heated build volume/chamber
        :param heating_zone: Zone selection - "bed_only" or "bed_chamber"
        :param max_y: Maximum Y axis position for parking as string
        :param max_z: Maximum Z axis position (machine height - 20mm) as string
        :param speed_travel: Travel speed for positioning moves in mm/min as string
        :return: Modified G-code data containing only filament drying sequence
        """
        for num in range(2, len(drydata)):
            drydata[num] = ""
        drydata[0] = drydata[0].split("\n")[0] + "\n"
        add_messages = bool(self.getSettingValueByKey("add_messages"))
        pause_cmd = self.getSettingValueByKey("pause_cmd")
        if pause_cmd != "":
            pause_cmd = self.beep_string + pause_cmd
        dry_time = self.getSettingValueByKey("dry_time") * 3600
        lines = drydata[1].split("\n")
        drying_string = lines[0] + f"\n;............TYPE:CUSTOM: Dry Filament\n{self.beep_string}"
        if add_messages:
            drying_string += f"M117 Cool Down for {round(dry_time/3600,2)} hr ; Message\n"
            drying_string += f"M118 Cool Down for {round(dry_time/3600,2)} hr ; Message\n"

        # M113 sends messages to a print server as a 'Keep Alive' and can generate a lot of traffic over the USB
        drying_string += "M113 S0 ; No echo\n"
        drying_string += f"M84 S{round(dry_time)} ; Set stepper timeout\n"
        drying_string += f"M140 S{bed_temperature} ; Heat bed\n"
        drying_string += self.bv_fan_on_str
        if heated_chamber and heating_zone == "bed_chamber":
            drying_string += f"M141 S{chamber_temp} ; Chamber temp\n"
        if pause_cmd == "M0":
            pause_cmd = "M0 Clear bed and click...; Pause"
        if pause_cmd != "":
            drying_string += pause_cmd + " ; Pause\n"
        drying_string += "G28 ; Auto-Home\n"
        drying_string += f"G0 F{speed_travel} Z{max_z} ; Raise Z to 'ZMax - 20'\n"
        drying_string += f"G0 F{speed_travel} X0 Y{max_y} ; Park print head\n"
        if dry_time <= 3600:
            if add_messages:
                drying_string += f"M117 {dry_time/3600} hr remaining ; Message\n"
                drying_string += f"M118 {dry_time/3600} hr remaining ; Message\n"
            drying_string += f"G4 S{dry_time} ; Dry time\n"
        elif dry_time > 3600:
            temp_time = dry_time
            while temp_time > 3600:
                if add_messages:
                    drying_string += f"M117 {temp_time/3600} hr remaining ; Message\n"
                    drying_string += f"M118 {temp_time/3600} hr remaining ; Message\n"
                drying_string += f"G4 S3600 ; Dry time split\n"
                if temp_time > 3600:
                    temp_time -= 3600
            if temp_time > 0:
                if add_messages:
                    drying_string += f"M117 {temp_time/3600} hr remaining ; Message\n"
                    drying_string += f"M118 {temp_time/3600} hr remaining ; Message\n"
                drying_string += f"G4 S{temp_time} ; Dry time\n"
        if heated_chamber and heating_zone == "bed_chamber":
            drying_string += f"M141 S0 ; Shut off chamber\n"
        drying_string += "M140 S0 ; Shut off bed\n"
        drying_string += self.bv_fan_off_str
        if self.getSettingValueByKey("beep_when_done"):
            beep_duration = self.getSettingValueByKey("beep_duration")
            drying_string += self.beep_string
        if add_messages:
            drying_string += "M117 End of drying cycle ; Message\n"
            drying_string += "M118 End of drying cycle ; Message\n"
        drying_string += "M84 X Y E ; Disable steppers except Z\n"
        drying_string += ";End of Gcode"

        # Format the lines
        lines = drying_string.split("\n")
        for index, line in enumerate(lines):
            if not line.startswith(";") and ";" in line:
                front_txt = lines[index].split(";")[0]
                back_txt = lines[index].split(";")[1]
                lines[index] = front_txt + str(" " * (30 - len(front_txt))) +";" +  back_txt
        drydata[1] = "\n".join(lines) + "\n"
        dry_txt = "; Drying time ...................... " + str(self.getSettingValueByKey("dry_time")) + " hrs\n"
        dry_txt += "; Drying temperature ........ " + str(bed_temperature) + "°\n"
        if heated_chamber and heating_zone == "bed_chamber":
            dry_txt += "; Chamber temperature ... " + str(chamber_temp) + "°\n"
        Message(title = "[Dry Filament]", text = dry_txt).show()
        drydata[0] = "; <<< This is a filament drying file only. There is no actual print. >>>\n;\n" + dry_txt + ";\n"
        return drydata
