# Created by Jonny Graham

from ..Script import Script

class AdjustSupportFlow(Script):
    NOT_IN_SUPPORT = 0
    IN_SUPPORT = 1
    def __init__(self):
        super().__init__()
        self.state = self.NOT_IN_SUPPORT
        self.last_e_value = None
        self.last_adj_e_value = None
        self.was_retracted = False

    def getSettingDataString(self):
        return """{
            "name": "Adjust Support Flow",
            "key": "AdjustSupportFlow",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "start_layer_number":
                {
                    "label": "From Layer",
                    "description": "From what layer should the flow adjustment be applied.",
                    "unit": "",
                    "type": "int",
                    "default_value": 2
                },
                "flow_adjust_percentage":
                {
                    "label": "Support flow percentage",
                    "description": "The required percentage to use to reduce flow rate when printing the support parts. Note that this percentage is not absolute but relative to the flow in the model.",
                    "unit": "",
                    "type": "float",
                    "default_value": 75
                }
            }
        }"""


    def __process_line__(self,line, flow_adjust_multiplier):
        new_line = line
        if self.state == self.NOT_IN_SUPPORT:
            if line.startswith(";TYPE:SUPPORT"):
                self.state = self.IN_SUPPORT
                self.last_e_value = None
                self.was_retracted = False
                new_line=new_line+"\n;AdjustSupportFlow start adjusting"
        elif self.state == self.IN_SUPPORT:
            if line.startswith(";TYPE:"):
                # Reset the extruder value
                new_line = ";AdjustSupportFlow reset E\n"+self.putValue(G=92,E=self.last_e_value)+"\n"+new_line
                if line.startswith(";TYPE:SUPPORT"):
                    new_line=new_line+"\n;AdjustSupportFlow start adjusting"
                    self.last_e_value = None
                    self.was_retracted = False
                else:
                    self.state = self.NOT_IN_SUPPORT
                    new_line=";AdjustSupportFlow stop adjusting\n"+new_line
            else:
                e_value = self.getValue(line,"E")
                if e_value is not None:
                    if self.last_e_value == None:
                        self.last_e_value = e_value
                        self.last_adj_e_value = e_value
                    else:
                        e_value_delta = e_value - self.last_e_value
                        if e_value_delta < 0 or self.was_retracted: # ie retraction or un-retraction
                            multiplier = 1 # Don't scale the flow during retraction 
                            self.was_retracted = not self.was_retracted
                        else:
                            multiplier = flow_adjust_multiplier
                        adj_e_value = self.last_adj_e_value + (e_value - self.last_e_value) * multiplier
                        self.last_e_value = e_value
                        self.last_adj_e_value = adj_e_value
                        new_line = self.putValue(line,E=adj_e_value)
        return new_line

    def execute(self, data):
        start_layer_number = self.getSettingValueByKey("start_layer_number")
        start_gcode_index = int(start_layer_number) + 1 # (+2) First two 'data' rows are pre-layer and (-1) the layers are indexed from 1 in Cura UI
        flow_adjust_percentage = self.getSettingValueByKey("flow_adjust_percentage")
        flow_adjust_multiplier = float(flow_adjust_percentage) / 100
        gcode_index = 0
        for layer in data:
            if gcode_index >= start_gcode_index:
                lines = layer.split("\n")
                new_layer = ""
                self.state = self.NOT_IN_SUPPORT
                for line in lines:
                    new_layer += self.__process_line__(line,flow_adjust_multiplier) + "\n"
                data[gcode_index] = new_layer.rstrip("\n")
            gcode_index += 1
        return data