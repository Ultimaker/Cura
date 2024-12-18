# Copyright (c) 2017 Ghostkeeper
# The PostProcessingPlugin is released under the terms of the LGPLv3 or higher.
# Altered by GregValiant (Greg Foresi) February, 2023.
#    Added option for a layer search with a Start Layer and an End layer.
#    Added 'Ignore StartUp G-code' and 'Ignore Ending G-code' options

import re
from ..Script import Script
from UM.Application import Application

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
                    "description": "The 'Search For' text will get replaced by this text.  For Multi-Line insertions use the newline character 'backslash plus n' as the delimiter. If your Search term ends with a '\n' remember to add '\n' to the end of the Replace term.",
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
                    "description": "Use the Cura Preview layer numbering.  The Start Layer will be included. Enter '1' to start with gcode ';LAYER:0'. Enter ''-6'' to start with the first layer of a raft.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": -6,
                    "enabled": "enable_layer_search"
                },
                "search_end":
                {
                    "label": "Stop S&R at end of Layer:",
                    "description": "Use the Cura Preview layer numbering.  Enter '-1' to search and replace to the end of the file.  Enter any other layer number and the replacements will conclude at the end of that layer.  If the End Layer is equal to the Start Layer then only that single layer is searched.",
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
        curaApp = Application.getInstance().getGlobalContainerStack()
        extruder = curaApp.extruderList
        retract_enabled = bool(extruder[0].getProperty("retraction_enable", "value"))
        # If retractions are enabled then the CuraEngine inserts a single data item for the retraction at the end of the last layer
        # 'top_layer' accounts for that
        if retract_enabled:
            top_layer = 2
        else:
            top_layer = 1
        search_string = self.getSettingValueByKey("search")
        replace_string = self.getSettingValueByKey("replace")
        is_regex = self.getSettingValueByKey("is_regex")
        enable_layer_search = self.getSettingValueByKey("enable_layer_search")
        start_layer = self.getSettingValueByKey("search_start")
        end_layer = self.getSettingValueByKey("search_end")
        ignore_start = self.getSettingValueByKey("ignore_start")
        ignore_end = self.getSettingValueByKey("ignore_end")
        if enable_layer_search:
            ignore_start = True
            ignore_end = True
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
            pass
    #Determine the actual start and end indexes of the data----------------------------------------------------
        try:
            if not enable_layer_search:
                if ignore_start:
                    start_index = 2
                else:
                    start_index = 1
                if ignore_end:
                    end_index = len(data) - top_layer
                else:
                    end_index = len(data)
            elif enable_layer_search:
                if start_layer < 1 and start_layer != -6:
                    start_index = layer_0_index - raft_layers
                elif start_layer == -6:
                    start_index = 2
                else:
                    start_index = raft_start_index + start_layer - 1
                if end_layer == -1:
                    end_index = len(data) - top_layer
                else:
                    end_index = raft_start_index + int(end_layer)
                if end_index > len(data) - 1: end_index = len(data) - 1 #For possible user input error
                if int(end_index) < int(start_index): end_index = start_index #For possible user input error
        except:
            start_index = 2
            end_index = len(data) - top_layer

    # If "first_instance_only" is enabled:
        replaceone = False
        if first_instance_only:
            if not is_regex:
                search_string = re.escape(search_string)
            search_regex = re.compile(search_string)
            for num in range(start_index, end_index, 1):
                layer = data[num]
                if re.search(search_regex, layer) and replaceone == False:
                    data[num] = re.sub(search_regex, replace_string, data[num], 1)
                    replaceone = True
                    break
                if replaceone: break
            return data

    # For all the replacements
        if not is_regex:
            search_string = re.escape(search_string)
        search_regex = re.compile(search_string)
        if end_index > start_index:
            for index in range(start_index, end_index, 1):
                layer = data[index]
                data[index] = re.sub(search_regex, replace_string, layer)
        elif end_index == start_index:
            layer = data[start_index]
            data[start_index] = re.sub(search_regex, replace_string, layer)
        return data
