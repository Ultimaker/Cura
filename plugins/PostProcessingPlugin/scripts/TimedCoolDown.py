# Copyright (c) 2023 GregValiant
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.
# The user can elect to hold the bed temperature for a period of time after the print completes.
# Then the bed (and heated chamber) can be allowed to cool in 3° increments over a period of time.

from UM.Application import Application
from ..Script import Script
from UM.Message import Message

class TimedCoolDown(Script):
    """Performs a search-and-replace on the g-code.
    """
    def __init__(self):
        super().__init__()
    
    def getSettingDataString(self):
        return """{
            "name": "Timed Cool Down Period",
            "key": "TimedCoolDown",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "bed_and_chamber":
                {
                    "label": "Hold the Temp for the:",
                    "description": "Hold the Bed temp (and) Heated Chamber temp at the final temperature for this amount of time (in decimal hours).  When this time expires the timed cool down will start.",
                    "type": "enum",
                    "options":
                    {
                        "bed_only": "Bed",
                        "bed_chamber": "Bed and Chamber"},
                    "default_value": "bed_only"
                },
                "wait_time":
                {
                    "label": "Hold Time (@Bed/Chamber Temp):",
                    "description": "Hold the bed temp at the finish temperature for this amount of time (in decimal hours).  When the time expires the timed cool down will start.",
                    "type": "float",
                    "default_value": 0,
                    "unit": "Decimal Hrs "
                },
                "lowest_temp":
                {
                    "label": "Shut-Off Temp:",
                    "description": "Enter the lowest temperature to control the cool down.  This is the shut-off temperature for the build plate and (when applicable) the Heated Chamber.",
                    "type": "int",
                    "default_value": 30,
                    "unit": "Degrees ",
                    "minimum_value": 30
                },
                "time_span":
                {
                    "label": "Cool Down Time Span:",
                    "description": "The total amount of time (in decimal hours) to control the cool down.  The build plate temperature will be dropped in 3° increments across this time span.",
                    "type": "float",
                    "default_value": 1.0,
                    "unit": "Decimal Hrs ",
                    "minimum_value_warning": 0.25
                },
                "park_head":
                {
                    "label": "Park at MaxY and MaxZ",
                    "description": "Move to Max Y and Max Z.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "beep_when_done":
                {
                    "label": "Beep when done",
                    "description": "Add an annoying noise when the Cool Down completes.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "beep_duration":
                {
                    "label": "Beep Duration",
                    "description": "The length of the buzzer sound.  Units are in milliseconds so 1000ms = 1 second.",
                    "type": "int",
                    "unit": "milliseconds ",
                    "default_value": 1000,
                    "enabled": "beep_when_done"
                }
            }
        }"""
             
    def execute(self, data):
        # Exit if there is no heated bed.
        if not bool(Application.getInstance().getGlobalContainerStack().getProperty("machine_heated_bed", "value")):
            Message(text = "Timed Cool Down:" + "\n" + "  Did not run because Heated Bed is disabled in Machine Settings.").show()
            return data
        lowest_temp = int(self.getSettingValueByKey("lowest_temp"))
        
        #If the shutoff temp is under 30° then exit as a safety precaution so the bed doesn't stay on.
        if lowest_temp < 30:
            data[0] += ";  Timed Cool Down did not run.  Shutoff Temp < 30\n"
            Message(text = "Timed Cool Down did not run because the Shutoff Temp is less than 30°.").show()     
            return data
        time_span = int(float(self.getSettingValueByKey("time_span")) * 3600)
        bed_temperature = Application.getInstance().getGlobalContainerStack().getProperty("material_bed_temperature", "value")
        heated_chamber = bool(Application.getInstance().getGlobalContainerStack().getProperty("machine_heated_build_volume", "value"))            
        anneal_type = self.getSettingValueByKey("bed_and_chamber")
        
        # Get the heated chamber temperature or set to 0 if there isn't one----------------------------
        if heated_chamber:
            chamber_temp = str(Application.getInstance().getGlobalContainerStack().getProperty("build_volume_temperature", "value"))
        else:
            anneal_type = "bed_only"
            chamber_temp = "0"
        
        # If Park Head is selected---------------------------------------------------------
        if bool(self.getSettingValueByKey("park_head")):
            max_Y = str(Application.getInstance().getGlobalContainerStack().getProperty("machine_depth", "value"))
            max_Z = str(Application.getInstance().getGlobalContainerStack().getProperty("machine_height", "value"))
            extruder = Application.getInstance().getGlobalContainerStack().extruderList
            travel_speed = str(extruder[0].getProperty("speed_travel", "value")*60)
            park_string = "G0 F" + str(travel_speed) + " Y" + str(max_Y) + " Z" + str(max_Z) + "\n" + "M18 X Y E ;disable steppers except Z\n"
        else:
            park_string = ""
            
        #Calculate the temperature differential
        hysteresis = bed_temperature - lowest_temp
        
        #if the bed temp is below the shutoff temp then exit
        if hysteresis <= 0:
            data[0] += ";  Timed Cool Down did not run.  Bed Temp < Shutoff Temp\n"
            Message(text = "Timed Cool Down: {}".format("Did not run because the Bed Temp < Shutoff Temp.")).show()
            return data
        
        # Drop the bed temperature in 3° increments.  We only want integers.
        num_steps = int(hysteresis / 3)
        step_index = 2
        deg_per_step = int(hysteresis / num_steps)
        time_per_step = int(time_span / num_steps)
        step_down = bed_temperature - deg_per_step
        wait_time = int(float(self.getSettingValueByKey("wait_time")) * 3600)
        
        #Put the first lines of the anneal string together--------------------------------------
        anneal_string = ";TYPE:CUSTOM:Timed Cool Down\nM117 Cool Down for " + str(round((wait_time + time_span)/3600,2)) + "hr\n" + park_string
        if wait_time > 0:
            if anneal_type == "bed_only":
                anneal_string += "M140 S" + str(bed_temperature) + "\n"
            if anneal_type == "bed_chamber":
                anneal_string += "M140 S" + str(bed_temperature) + "\n" + "M141 S" + str(chamber_temp) + "\n"
            anneal_string += "G4 S" + str(wait_time) + "\n"            
        anneal_string += "M140 S" + str(step_down) + "\n" + "G4 S" + str(time_per_step) + "\n"
        step_down -= deg_per_step
        
        # Step the bed/chamber temps down and add to the anneal string--------------------------
        for num in range(bed_temperature,lowest_temp, -3):
            anneal_string += "M140 S" + str(step_down) + "\n"
            if anneal_type == "bed_chamber" and int(step_down) < int(chamber_temp):
                anneal_string += "M141 S" + str(step_down) + "\n"
            anneal_string += "G4 S" + str(time_per_step) + "\n"
            anneal_string += "M117 CoolDown for " + str(round((time_span-(step_index*time_per_step))/3600,2)) + "hr\n"
            step_down -= deg_per_step
            step_index += 1
            if step_down < lowest_temp:
                break
                
        # Maybe add the Beep line--------------------------------------------------------
        if bool(self.getSettingValueByKey("beep_when_done")):
            beep_string = "M300 S440 P" + str(self.getSettingValueByKey("beep_duration")) + "\n"
        else:
            beep_string = ""
        # Close out the anneal string----------------------------------------------------
        anneal_string += "M140 S0 ;Shut off the bed heater" + "\n"
        if anneal_type == "bed_chamber":
            anneal_string += "M141 S0 ;Shut off the chamber heater\n"
        anneal_string += beep_string + "M117 CoolDown Complete\n;  End of Cool Down\n"
        layer = data[len(data)-1]
        lines = layer.split("\n")
        
        #comment out the M140 S0 line in the ending gcode.
        for num in range(len(lines)-1,-1,-1):
            if lines[num].startswith("M140 S0"):
                lines[num] = ";M140 S0 ;Overide - Timed Cool Down"
                data[len(data)-1] = "\n".join(lines)
                
        # if there is a Heated Chamber and it's included then comment out the M141 S0 line-----------------
        if anneal_type == "bed_chamber" and heated_chamber:
            for num in range(0,len(lines)-1,1):
                if lines[num].startswith("M141 S0"):
                    lines[num] = ";M141 S0 ;Overide - Timed Cool Down"
                    data[len(data)-1] = "\n".join(lines)
                    
        # If park head is enabled then dont let the steppers disable until the head is parked--------------
        disable_string = ""
        if bool(self.getSettingValueByKey("park_head")):
            for num in range(0,len(lines)-1,1):
                if lines[num].startswith("M84") or lines[num].startswith("M18"):
                    disable_string = lines[num] + "\n"
                    stepper_timeout = int(wait_time + time_span)
                    if stepper_timeout > 14400: stepper_timeout = 14400
                    lines[num] = ";" + lines[num] + " ;Overide - Timed Cool Down"
                    lines.insert(num, "M18 S" + str(stepper_timeout) + " ;increase stepper timeout - Timed Cool Down")
                    data[len(data)-1] = "\n".join(lines)                    
                    break
        #The Anneal string is the new end of the gcode so move the comment line in case there are other posts running
        data[len(data)-1] = data[len(data)-1].replace(";End of Gcode" + "\n", "")     
        
        #Add the Anneal string to the end of the gcode and re-insert the ';End of Gcode' line.
        data[len(data)-1] += anneal_string + disable_string + ";End of Gcode" + "\n"
        return data