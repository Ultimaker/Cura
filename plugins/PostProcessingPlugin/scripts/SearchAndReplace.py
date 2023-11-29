# Copyright (c) 2017 Ghostkeeper
# The PostProcessingPlugin is released under the terms of the LGPLv3 or higher.
# Altered by GregValiant (Greg Foresi) February, 2023.
#    Added option for a layer search with a Start Layer and an End layer.
#    Added 'Ignore StartUp G-code' and 'Ignore Ending G-code' options

import re #To perform the search and replace.
from ..Script import Script

class SearchAndReplace(Script):
    """Performs a search-and-replace on the g-code.
    """

    def getSettingDataString(self):
        return """{
            "name": "Search and Replace",
            "key": "SearchAndReplace",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "search":
                {
                    "label": "Search for:",
                    "description": "All occurrences of this text (within the search range) will be replaced by the 'Replace with' text.  The search string is CASE SPECIFIC so 'LAYER' is not the same as 'layer'.",
                    "type": "str",
                    "default_value": ""
                },
                "replace":
                {
                    "label": "Replace with:",
                    "description": "The 'Search For' text will get replaced by this text.  For Multi-Line insertions use the newline character 'backslash plus n' as the delimiter. Also for multi-line insertions the last character must be 'backslash plus n'",
                    "type": "str",
                    "default_value": ""
                },
                "is_regex":
                {
                    "label": "Use Regular Expressions",
                    "description": "When disabled the search string is treated as a simple text string.  When enabled, the search text will be re-compiled as a 'regular' python expression.",
                    "type": "bool",
                    "default_value": false
                },
                "enable_layer_search":
                {
                    "label": "Enable search within a Layer Range:",
                    "description": "When enabled, You can choose a Start and End layer for the search.  When 'Layer Search' is enabled the StartUp and Ending g-codes are always ignored.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "search_start":
                {
                    "label": "Start S&R at Layer:",
                    "description": "Use the Cura Preview layer numbering.  The Start Layer will be included. Enter '1' to start with gcode ';LAYER:0'. Enter ''-6'' to start with the first layer of a raft",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": -6,
                    "enabled": "enable_layer_search"
                },
                "search_end":
                {
                    "label": "Stop S&R at end of Layer:",
                    "description": "Use the Cura Preview layer numbering.  Enter ''end'' to replace to the end of the file.  Enter any other layer number and the replacements will conclude at the end of that layer.",
                    "type": "int",
                    "default_value": -1,
                    "minimum_value": -1,
                    "enabled": "enable_layer_search"
                },
                "first_instance_only":
                {
                    "label": "Replace first instance only:",
                    "description": "When enabled only the first instance is replaced.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "ignore_start":
                {
                    "label": "Ignore StartUp G-code:",
                    "description": "When enabled the StartUp G-code is unaffected.  The StartUp G-code is everything from ';generated with Cura...' to ';LAYER_COUNT:' inclusive.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "not enable_layer_search"
                },
                "ignore_end":
                {
                    "label": "Ignore Ending G-code:",
                    "description": "When enabled the Ending G-code is unaffected.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "not enable_layer_search"
                }
            }
        }"""

    def execute(self, data):
        search_string = self.getSettingValueByKey("search")
        replace_string = self.getSettingValueByKey("replace")
        is_regex = self.getSettingValueByKey("is_regex")
        enable_layer_search = self.getSettingValueByKey("enable_layer_search")
        start_layer = self.getSettingValueByKey("search_start")
        end_layer = self.getSettingValueByKey("search_end")
        ignore_start = self.getSettingValueByKey("ignore_start")
        ignore_end = self.getSettingValueByKey("ignore_end")
        first_instance_only = bool(self.getSettingValueByKey("first_instance_only"))

    #Find the raft and layer:0 indexes--------------------------------------------------------------------------
        raft_start_index = 0
        layer_0_index = 0
        start_index = 1
        end_index = len(data)
        try:
            for l_num in range(2,12,1):
                layer = data[l_num]
                if ";LAYER:-" in layer and raft_start_index == 0:
                    raft_start_index = l_num
                if ";LAYER:0" in layer:
                    layer_0_index = l_num
                    break
            if raft_start_index == 0:
                raft_start_index = layer_0_index
                raft_layers = 0
            elif raft_start_index < layer_0_index:
                raft_layers = layer_0_index - raft_start_index
            else:
                raft_layers = 0
        except:
            all
            
    #Determine the actual start and end indexes of the data----------------------------------------------------
        try:
            if not enable_layer_search:
                if ignore_start:
                    start_index = 2
                else:
                    start_index = 1
                if ignore_end:
                    end_index = len(data) - 1
                else:
                    end_index = len(data)
            elif enable_layer_search:
                if start_layer < 1 and start_layer != -6:
                    start_index = layer_0_index - raft_layers
                elif start_layer == -6:
                    start_index = 2
                else:
                    start_index = raft_start_index + start_layer-1
                if end_layer == -1:
                    end_index = len(data)-1
                else:
                    end_index = raft_start_index + int(end_layer)
                if end_index > len(data)-1: end_index = len(data)-1 #For possible Input error
                if int(end_layer) < int(start_layer): end_index = start_index #For possible Input error
        except:
            start_index = 2
            end_index = len(data) -1

    #if "first_instance_only" is enabled:
        replaceone = False
        new_string = search_string
        if first_instance_only:
            if not is_regex:
                new_string = re.escape(search_string)
            search_regex = re.compile(new_string)
            for num in range(start_index, end_index,1):
                layer = data[num]
                lines = layer.split("\n")
                for index, line in enumerate(lines):
                    if re.match(search_regex, line) and replaceone == False:
                        lines[index] = re.sub(search_regex, replace_string, line)
                        data[num] = "\n".join(lines)
                        replaceone = True
                        break
                if replaceone: break
            return data
            
    #Do all the replacements---------------------------------------------------------------------------------------
        if not is_regex:
            search_string = re.escape(search_string)
        search_regex = re.compile(search_string)
        if end_index > start_index:
            for index in range(start_index,end_index,1):
                layer = data[index]
                data[index] = re.sub(search_regex, replace_string, layer)
        elif end_index == start_index:
            layer = data[start_index]
            data[start_index] = re.sub(search_regex, replace_string, layer)
        return data
        