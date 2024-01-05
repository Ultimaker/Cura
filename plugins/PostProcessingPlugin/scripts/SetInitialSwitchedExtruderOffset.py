# Copyright (c) 2022 Anson Liu
# This script is released under the terms of the AGPLv3 or higher.

from ..Script import Script
from UM.Logger import Logger
from UM.Message import Message
from cura.CuraApplication import CuraApplication
import re

class ExtruderInitialOffsetInfo:
  def __init__(self, offset_complete, switch_extruder_retraction_amount, switch_extruder_prime_speed, switch_extruder_extra_prime_amount, retraction_distance):
    self.offset_complete = offset_complete
    self.switch_extruder_retraction_amount = switch_extruder_retraction_amount
    self.switch_extruder_prime_speed = switch_extruder_prime_speed
    self.switch_extruder_extra_prime_amount = switch_extruder_extra_prime_amount
    self.retraction_distance = retraction_distance

class SetInitialSwitchedExtruderOffset(Script):
    """Adds timed annealing GCODE after objects finish printing.

    Bed annealing works best with a glass bed and a container placed on top of the object during annealing.
    """
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name": "Set Initial Switched Extruder Offset",
            "key": "SetInitialSwitchedExtruderOffset",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "addSwitchExtruderExtraPrimeAmount":
                {
                    "label": "Add Nozzle Switch Extra Prime Amount to Offset",
                    "description": "Offset the initial offset of the extruder by an additional length equal to that extruder's Nozzle Switch Extra Prime Amount.",
                    "type": "bool",
                    "default_value": true
                },
                "setT0ExtruderOffset":
                {
                    "label": "Set Extruder 1 Offset",
                    "description": "Set the initial offset of this extruder by Nozzle Switch Retraction Distance. If this extruder was previously switched out and retracted, this will ensure filament flow the first time this extruder is using this print. If your machine primes the initial extruder, the initial extruder does not need an offset.",
                    "type": "bool",
                    "default_value": false
                },
                "setT1ExtruderOffset":
                {
                    "label": "Set Extruder 2 Offset",
                    "description": "",
                    "type": "bool",
                    "default_value": "CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr() != 1"
                },
                "setT2ExtruderOffset":
                {
                    "label": "Set Extruder 3 Offset",
                    "description": "",
                    "type": "bool",
                    "default_value": "CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr() != 2"
                },
                "setT3ExtruderOffset":
                {
                    "label": "Set Extruder 4 Offset",
                    "description": "",
                    "type": "bool",
                    "default_value": "CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr() != 3"
                },
                "setT4ExtruderOffset":
                {
                    "label": "Set Extruder 5 Offset",
                    "description": "",
                    "type": "bool",
                    "default_value": "CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr() != 4"
                },"setT5ExtruderOffset":
                {
                    "label": "Set Extruder 6 Offset",
                    "description": "",
                    "type": "bool",
                    "default_value": "CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr() != 5"
                },"setT6ExtruderOffset":
                {
                    "label": "Set Extruder 7 Offset",
                    "description": "",
                    "type": "bool",
                    "default_value": "CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr() != 6"
                },"setT7ExtruderOffset":
                {
                    "label": "Set Extruder 8 Offset",
                    "description": "",
                    "type": "bool",
                    "default_value": "CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr() != 7"
                },"setT8ExtruderOffset":
                {
                    "label": "Set Extruder 9 Offset",
                    "description": "",
                    "type": "bool",
                    "default_value": "CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr() != 8"
                },"setT9ExtruderOffset":
                {
                    "label": "Set Extruder 10 Offset",
                    "description": "",
                    "type": "bool",
                    "default_value": "CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr() != 9"
                }
            }
        }"""

    def execute(self, data):
        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()

        initial_extruder_nr = CuraApplication.getInstance().getExtruderManager().getInitialExtruderNr()

        extruderOffsetInfo = []
        for e_index in range(0, len(global_container_stack.extruderList)):
            setExtruderOffset = False
            if e_index < 10:
              setExtruderOffset = self.getSettingValueByKey(f"setT{e_index}ExtruderOffset")

            extruder = global_container_stack.extruderList[e_index]

            extruderOffsetInfo.append(
                ExtruderInitialOffsetInfo(
                    offset_complete=not setExtruderOffset,
                    switch_extruder_retraction_amount=extruder.getProperty('switch_extruder_retraction_amount', 'value'),
                    switch_extruder_prime_speed=extruder.getProperty('switch_extruder_prime_speed', 'value'),
                    switch_extruder_extra_prime_amount=extruder.getProperty('switch_extruder_extra_prime_amount', 'value'),
                    retraction_distance=extruder.getProperty('retraction_amount', 'value')
                )
            )

        addSwitchExtruderExtraPrimeAmount = self.getSettingValueByKey("addSwitchExtruderExtraPrimeAmount")

        def generateTCmd(e_index):
            return f"T{e_index}"

        def generateG92Cmd(extruder_offset):
            return f"G92 E{extruder_offset}"
        
        def generateG1Cmd(feedrate, extruder_offset):
            return f"G1 F{feedrate} E{extruder_offset}"
        
        g1_extrude = "^G1 (F\d+)? E-?\d+"

        for index_num in range(2,len(data)-1,1):
          layer = data[index_num]
          lines = layer.split("\n")

          for e_index in range(0, len(extruderOffsetInfo)):
              if extruderOffsetInfo[e_index].offset_complete:
                  continue

              current_line_nr = -1
              found_layer_number = False
              found_toolchange_cmd = False
              found_g92_e0_cmd = False
              found_g1_extrude_cmd = False
              for line in lines:
                  # If found g1 extrude cmd, then changes for this layer for this extruder are done
                  if found_g1_extrude_cmd: 
                      break

                  current_line_nr += 1
                  if found_layer_number == False:
                      if line.startswith(";LAYER:"):
                          layer_number = str(line.split(":")[1])
                          if int(layer_number) >= int(0):
                              found_layer_number = True
                              continue
                      continue
                  if found_toolchange_cmd == False:
                      if line.startswith(generateTCmd(e_index)):
                          found_toolchange_cmd = True
                          continue
                      continue
                  if found_g92_e0_cmd == False:
                      if line == generateG92Cmd(0):
                          found_g92_e0_cmd = True
                          lines[current_line_nr] = generateG92Cmd(-(extruderOffsetInfo[e_index].switch_extruder_retraction_amount+(extruderOffsetInfo[e_index].switch_extruder_extra_prime_amount if addSwitchExtruderExtraPrimeAmount else 0))) + \
                              " ; SetInitialExtruderOffset: Set extruder offset to switch_extruder_retraction_amount+switch_extruder_extra_prime_amount"
                          extruderOffsetInfo[e_index].offset_complete = True
                          continue
                      continue
                  if found_g1_extrude_cmd == False:
                      if re.match(g1_extrude, line):
                          found_g1_extrude_cmd = True
                          lines[current_line_nr] = generateG1Cmd(extruderOffsetInfo[e_index].switch_extruder_prime_speed*60, -extruderOffsetInfo[e_index].retraction_distance) + \
                              " ; SetInitialExtruderOffset: Changed feedrate of nozzle prime to switch_extruder_prime_speed"
                          break
                      continue
              
          layer = "\n".join(lines)
          data[index_num] = layer
        return data
