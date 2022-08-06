# Copyright (c) 2022 Anson Liu
# The PostProcessingPlugin is released under the terms of the AGPLv3 or higher.

from ..Script import Script

class AnnealAfterPrint(Script):
    """Adds timed annealing GCODE after objects finish printing.

    Bed annealing works best with a glass bed and a container placed on top of the object during annealing.
    """

    def getSettingDataString(self):

        return """{
            "name": "Anneal After Print",
            "key": "AnnealAfterPrint",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "heatingElement":
                {
                    "label": "Heating Element",
                    "description": "Printer heating element to use for annealing. Glass bed and 4-8 mm brim is recommended if XY dimensional stability is desired.",
                    "type": "enum",
                    "options":
                    {
                        "bed": "Bed",
                        "chamber": "Chamber",
                        "all": "Bed and Chamber"
                    },
                    "default_value": "bed"
                },
                "annealBedTemp":
                {
                    "label": "Bed Temperature",
                    "description": "Bed temperature annealing. Recommended bed temperature is greater of build plate printing or vendor specified annealing temperature for material. Temperature should be between material glass transition temperature and melting point. E.g. PC 90-110 C, PLA 60-90 C",
                    "unit": "C",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": 0,
                    "enabled": "heatingElement == \\\"bed\\\" or heatingElement == \\\"all\\\""
                },
                "annealChamberTemp":
                {
                    "label": "Chamber Temperature",
                    "description": "Chamber temperature for annealing. Temperature should be between material glass transition temperature and melting point.",
                    "unit": "C",
                    "type": "float",
                    "default_value": 0,
                    "minimum_value": 0,
                    "enabled": "heatingElement == \\\"chamber\\\" or heatingElement == \\\"all\\\""
                },
                "annealMinutes":
                {
                    "label": "Annealing Target Temperature Duration",
                    "description": "Duration in minutes to anneal at target temperature. After duration ends gradually cool down to End Cooling Temperature.",
                    "unit": "min",
                    "type": "int",
                    "default_value": 120,
                    "minimum_value": 1
                },
                "reminderBeep":
                {
                    "label": "Beep on annealing start",
                    "description": "",
                    "type": "bool",
                    "default_value": false
                },
                "endCoolingTemp":
                {
                    "label": "End Cooling Temperature",
                    "description": "Temperature to end gradual cooling at after annealing at target temperature for specified duration.",
                    "unit": "C",
                    "type": "float",
                    "default_value": 50,
                    "minimum_value": 0
                },
                "coolingRate":
                {
                    "label": "Cooling Rate",
                    "description": "Gradual cooling rate. Temperature decreases by 1 C after specified seconds at each degree",
                    "unit": "sec/C",
                    "type": "int",
                    "default_value": 60,
                    "minimum_value": 0
                }
            }
        }"""

        settingData = settingData.format(anneal_temp_guideline)
        print(settingData)
        return settingData

    def generateAnnealCode(self, annealBedTemp, annealChamberTemp, annealMinutes, initialBeep, endCoolingTemp, coolingRate):
        anneal_code = ';Generated Annealing GCODE by Anson Liu'

        if initialBeep:
            anneal_code += '\nM300 ;play beep for container placement reminder'

        anneal_code += '\nM117 '
        if annealBedTemp:
            anneal_code += 'Place container over objects on bed. '
        anneal_code += 'Waiting until annealing temp reached...'
        anneal_code += '\nM73 P00 ;reset progress bar to 0'

        if annealBedTemp:
            anneal_code += '\nM190 R{} ;wait for buildplate to reach temp in C even if cooling'.format(annealBedTemp)
        if annealChamberTemp:
            anneal_code += '\nM191 R{} ;wait for chamber to reach temp in C even if cooling'.format(annealChamberTemp)

        anneal_code += '\nM117 '
        if annealBedTemp:
            anneal_code += 'Keep plastic container over objects. '
        anneal_code += 'Annealing...'
        anneal_code += '\nM73 P00' # reset progress bar to 0

        def generateDwellAndProgressCode(minutes): # Update progress bar and time every minute
            dp_code = 'M73 P0 R{}'.format(minutes)
            for x in range(1, minutes+1):
                dwellWaitSeconds = 60
                dp_code += '\nG4 S{}'.format(dwellWaitSeconds)
                progress = round(x/minutes * 100, 2)
                remainingMinutes = minutes - x
                dp_code += '\nM73 P{} R{}'.format(progress, remainingMinutes)

            return dp_code

        anneal_code += '\n' + generateDwellAndProgressCode(int(annealMinutes))
            
        anneal_code += '\nM117 Annealing complete. Gradually lowering bed temperature...'

        for x in reversed(range(endCoolingTemp, max(annealBedTemp, annealChamberTemp))):
            if annealBedTemp and annealBedTemp > x:
                anneal_code += '\nM190 S{}'.format(x) # Wait for buildplate only if heating
            if annealChamberTemp and annealChamberTemp > x:
                anneal_code += '\nM191 S{}'.format(x)
            anneal_code += '\nG4 S{}'.format(int(coolingRate)) # Wait user specified seconds after reaching each cooldown temperature

        if annealBedTemp:
            anneal_code += '\nM140 S0'
        if annealChamberTemp:
            anneal_code += '\nM141 S0'
        anneal_code += '\nM117 Annealing complete.'

        return anneal_code

    def execute(self, data):
        heating_element = self.getSettingValueByKey("heatingElement")

        # Set bed and chamber temp to true/false value based on heating element selection
        anneal_bed_temp = 0
        anneal_chamber_temp = 0
        if heating_element == "bed" or heating_element == "all":
            anneal_bed_temp = self.getSettingValueByKey("annealBedTemp")
        if heating_element == "chamber" or heating_element == "all":
            anneal_chamber_temp = self.getSettingValueByKey("annealChamberTemp")

        anneal_minutes = self.getSettingValueByKey("annealMinutes")
        initial_beep = self.getSettingValueByKey("reminderBeep")
        final_cooling_temp = self.getSettingValueByKey("endCoolingTemp")
        cooling_rate = self.getSettingValueByKey("coolingRate")

        # Test printing the generated anneal code
        #print(self.generateAnnealCode(110, 120, False, 50))
        anneal_code = self.generateAnnealCode(anneal_bed_temp, anneal_chamber_temp, anneal_minutes, initial_beep, final_cooling_temp, cooling_rate)

        try:
            end_of_gcode_index = data[-1].index(';End of Gcode')
        except ValueError:
            data[-1] += anneal_code + '\n'
        else:
            data[-1] = data[-1][:end_of_gcode_index] + anneal_code + '\n' + data[-1][end_of_gcode_index:]

        return data
