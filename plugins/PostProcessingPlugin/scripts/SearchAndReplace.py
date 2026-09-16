# Copyright (c) 2017 Ghostkeeper
# The PostProcessingPlugin is released under the terms of the LGPLv3 or higher.
# Altered by GregValiant (Greg Foresi) February, 2025.
#    Added option for "first instance only"
#    Added option for a layer search with a Start Layer and an End layer.
#    Added 'Ignore StartUp G-code' and 'Ignore Ending G-code' options

import re
from ..Script import Script
from UM.Application import Application

class SearchAndReplace(Script):
    """Performs a search-and-replace on the g-code.
    """

    def getSettingDataString(self):
        return r"""{
            "name": "Search and Replace",
            "key": "SearchAndReplace",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "search":
                {
                    "label": "Search for:",
                    "description": "All occurrences of this text (within the search range) will be replaced by the 'Replace with' string.  The search string is 'Case Sensitive' and 'Layer' is not the same as 'layer'.",
                    "type": "str",
                    "default_value": ""
                },
                "replace":
                {
                    "label": "Replace with:",
                    "description": "The 'Search For' text will get replaced by this text.  For MultiLine insertions use the newline character '\\n' as the delimiter. If your Search term ends with a '\\n' remember to add '\\n' to the end of this Replace term.",
                    "type": "str",
                    "default_value": ""
                },
                "is_regex":
                {
                    "label": "Use Regular Expressions",
                    "description": "When disabled the search string is treated as a simple text string.  When enabled, the search text will be interpreted as a Python regular expression.",
                    "type": "bool",
                    "default_value": false
                },
                "enable_layer_search":
                {
                    "label": "Enable search within a Layer Range:",
                    "description": "When enabled, You can choose a Start and End layer for the search.  When 'Layer Search' is enabled the StartUp and Ending gcodes are always ignored.",
                    "type": "bool",
                    "default_value": false,
                    "enabled": true
                },
                "search_start":
                {
                    "label": "Start S&R at Layer:",
                    "description": "Use the Cura Preview layer numbering.",
                    "type": "int",
                    "default_value": 1,
                    "minimum_value": 1,
                    "enabled": "enable_layer_search"
                },
                "search_end":
                {
                    "label": "Stop S&R at end of Layer:",
                    "description": "Use the Cura Preview layer numbering.  The replacements will conclude at the end of this layer.  If the End Layer is equal to the Start Layer then only that single layer is searched.",
                    "type": "int",
                    "default_value": 2,
                    "minimum_value": 1,
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
                    "description": "When enabled the StartUp Gcode is unaffected.  The StartUp Gcode is everything from ';generated with Cura...' to ';LAYER_COUNT:' inclusive.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "not enable_layer_search"
                },
                "ignore_end":
                {
                    "label": "Ignore Ending G-code:",
                    "description": "When enabled the Ending Gcode is unaffected.",
                    "type": "bool",
                    "default_value": true,
                    "enabled": "not enable_layer_search"
                }
            }
        }"""

    def execute(self, data):
        global_stack = Application.getInstance().getGlobalContainerStack()
        extruder = global_stack.extruderList
        retract_enabled = bool(extruder[0].getProperty("retraction_enable", "value"))
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

        # Account for missing layer numbers when a raft is used
        start_index = 1
        end_index = len(data) - 1
        data_list = [0,1]
        layer_list = [-1,0]
        lay_num = 1
        for index, layer in enumerate(data):
            if re.search(r";LAYER:(-?\d+)", layer):
                data_list.append(index)
                layer_list.append(lay_num)
                lay_num += 1

        # Get the start and end indexes within the data
        if not enable_layer_search:
            if ignore_start:
                start_index = 2
            else:
                start_index = 1

            if ignore_end:
                end_index = data_list[len(data_list) - 1]
            else:
                # Account for the extra data item when retraction is enabled
                end_index = data_list[len(data_list) - 1] + (2 if retract_enabled else 1)

        elif enable_layer_search:
            for index, num in enumerate(layer_list):
                if num == start_layer:
                    start_index = data_list[index]
                if num == end_layer:
                    end_index = data_list[index]

        # Make replacements
        replace_one = False
        if not is_regex:
            search_string = re.escape(search_string)
        search_regex = re.compile(search_string)
        for num in range(start_index, end_index + 1, 1):
            layer = data[num]
            # First_instance only
            if first_instance_only:
                if re.search(search_regex, layer) and replace_one == False:
                    data[num] = re.sub(search_regex, replace_string, data[num], 1)
                    replace_one = True
                    break
            # All instances
            else:
                if end_index > start_index:
                    data[num] = re.sub(search_regex, replace_string, layer)
                elif end_index == start_index:
                    layer = data[start_index]
                    data[start_index] = re.sub(search_regex, replace_string, layer)
        return data
