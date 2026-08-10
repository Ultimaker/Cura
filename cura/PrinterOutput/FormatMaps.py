# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

from UM.Resources import Resources

import json
from typing import Dict, List, Optional

class FormatMaps:

    # A map from the printer-type in their native file-formats to the internal name we use.
    PRINTER_TYPE_NAME = {
        "fire_e": "ultimaker_method",
        "lava_f": "ultimaker_methodx",
        "magma_10": "ultimaker_methodxl",
        "sketch": "ultimaker_sketch",
        "sketch_large": "ultimaker_sketch_large",
        "sketch_sprint": "ultimaker_sketch_sprint"
    }

    # A map from the extruder-name in their native file-formats to the internal name we use.
    EXTRUDER_NAME_MAP = {
        "mk14_hot": "1XA",
        "mk14_hot_s": "2XA",
        "mk14_c": "1C",
        "mk14": "1A",
        "mk14_s": "2A",
        "mk14_e": "LABS",
        "sketch_extruder": "0.4mm",
        "sketch_l_extruder": "0.4mm",
        "sketch_sprint_extruder": "0.4mm",
    }

    # A map from the material-name in their native file-formats to some info, including the internal name we use.
    MATERIAL_MAP = {
        "abs": {"name": "ABS", "guid": "e0f1d581-cc6b-4e36-8f3c-3f5601ecba5f"},
         "abs-cf10": {"name": "ABS-CF", "guid": "495a0ce5-9daf-4a16-b7b2-06856d82394d"},
         "abs-wss1": {"name": "ABS-R", "guid": "88c8919c-6a09-471a-b7b6-e801263d862d"},
         "asa": {"name": "ASA", "guid": "f79bc612-21eb-482e-ad6c-87d75bdde066"},
         "nylon": {"name": "Nylon", "guid": "9475b03d-fd19-48a2-b7b5-be1fb46abb02"},
         "nylon12-cf": {"name": "Nylon 12 CF", "guid": "3c6f2877-71cc-4760-84e6-4b89ab243e3b"},
         "nylon-cf": {"name": "Nylon CF", "guid": "17abb865-ca73-4ccd-aeda-38e294c9c60b"},
         "pet": {"name": "PETG", "guid": "2d004bbd-d1bb-47f8-beac-b066702d5273"},
         "pla": {"name": "PLA", "guid": "abb9c58e-1f56-48d1-bd8f-055fde3a5b56"},
         "pva": {"name": "PVA", "guid": "add51ef2-86eb-4c39-afd5-5586564f0715"},
         "wss1": {"name": "RapidRinse", "guid": "a140ef8f-4f26-4e73-abe0-cfc29d6d1024"},
         "sr30": {"name": "SR-30", "guid": "77873465-83a9-4283-bc44-4e542b8eb3eb"},
         "im-pla": {"name": "Tough", "guid": "de031137-a8ca-4a72-bd1b-17bb964033ad"}
         # /!\ When changing this list, make sure the changes are reported accordingly on Digital Factory
    }

    __inverse_printer_name: Optional[Dict[str, str]] = None
    __inverse_extruder_type: Optional[Dict[str, str]] = None
    __inverse_material_map: Optional[Dict[str, str]] = None
    __product_to_id_map: Optional[Dict[str, List[str]]] = None

    @classmethod
    def getInversePrinterNameMap(cls) -> Dict[str, str]:
        """Returns the inverse of the printer name map, that is, from the internal name to the name used in output."""
        if cls.__inverse_printer_name is not None:
            return cls.__inverse_printer_name
        cls.__inverse_printer_name = {}
        for key, value in cls.PRINTER_TYPE_NAME.items():
            cls.__inverse_printer_name[value] = key
        return cls.__inverse_printer_name

    @classmethod
    def getInverseExtruderTypeMap(cls) -> Dict[str, str]:
        """Returns the inverse of the extruder type map, that is, from the internal name to the name used in output."""
        if cls.__inverse_extruder_type is not None:
            return cls.__inverse_extruder_type
        cls.__inverse_extruder_type = {}
        for key, value in cls.EXTRUDER_NAME_MAP.items():
            cls.__inverse_extruder_type[value] = key
        return cls.__inverse_extruder_type

    @classmethod
    def getInverseMaterialMap(cls) -> Dict[str, str]:
        """Returns the inverse of the material map, that is, from the internal name to the name used in output.

        Note that this drops the extra info saved in the non-inverse material map, use that if you need it.
        """
        if cls.__inverse_material_map is not None:
            return cls.__inverse_material_map
        cls.__inverse_material_map = {}
        for key, value in cls.MATERIAL_MAP.items():
            cls.__inverse_material_map[value["name"]] = key
        return cls.__inverse_material_map

    @classmethod
    def getProductIdMap(cls) -> Dict[str, List[str]]:
        """Gets a mapping from product names (for example, in the XML files) to their definition IDs.

        This loads the mapping from a file.
        """
        if cls.__product_to_id_map is not None:
            return cls.__product_to_id_map

        product_to_id_file = Resources.getPath(Resources.Texts, "product_to_id.json")
        with open(product_to_id_file, encoding = "utf-8") as f:
            contents = ""
            for line in f:
                contents += line if "#" not in line else "".join([line.replace("#", str(n)) for n in range(1, 12)])
            cls.__product_to_id_map = json.loads(contents)
        cls.__product_to_id_map = {key: [value] for key, value in cls.__product_to_id_map.items()}
        #This also loads "Ultimaker S5" -> "ultimaker_s5" even though that is not strictly necessary with the default to change spaces into underscores.
        #However it is not always loaded with that default; this mapping is also used in serialize() without that default.
        return cls.__product_to_id_map
