# Copyright (c) 2024 UltiMaker
# Cura is released under the terms of the LGPLv3 or higher.

class FormatMaps:

    PRINTER_TYPE_NAME = {
        "fire_e": "ultimaker_method",
        "lava_f": "ultimaker_methodx",
        "magma_10": "ultimaker_methodxl",
        "sketch": "ultimaker_sketch"
    }

    EXTRUDER_NAME_MAP = {
        "mk14_hot": "1XA",
        "mk14_hot_s": "2XA",
        "mk14_c": "1C",
        "mk14": "1A",
        "mk14_s": "2A",
        "mk14_e": "LABS"
    }

    MATERIAL_MAP = {
        "abs": {"name": "ABS", "guid": "2780b345-577b-4a24-a2c5-12e6aad3e690"},
         "abs-cf10": {"name": "ABS-CF", "guid": "495a0ce5-9daf-4a16-b7b2-06856d82394d"},
         "abs-wss1": {"name": "ABS-R", "guid": "88c8919c-6a09-471a-b7b6-e801263d862d"},
         "asa": {"name": "ASA", "guid": "f79bc612-21eb-482e-ad6c-87d75bdde066"},
         "nylon12-cf": {"name": "Nylon 12 CF", "guid": "3c6f2877-71cc-4760-84e6-4b89ab243e3b"},
         "nylon": {"name": "Nylon", "guid": "283d439a-3490-4481-920c-c51d8cdecf9c"},
         "pc": {"name": "PC", "guid": "62414577-94d1-490d-b1e4-7ef3ec40db02"},
         "petg": {"name": "PETG", "guid": "69386c85-5b6c-421a-bec5-aeb1fb33f060"},
         "pla": {"name": "PLA", "guid": "abb9c58e-1f56-48d1-bd8f-055fde3a5b56"},
         "pva": {"name": "PVA", "guid": "add51ef2-86eb-4c39-afd5-5586564f0715"},
         "wss1": {"name": "RapidRinse", "guid": "a140ef8f-4f26-4e73-abe0-cfc29d6d1024"},
         "sr30": {"name": "SR-30", "guid": "77873465-83a9-4283-bc44-4e542b8eb3eb"},
         "bvoh": {"name": "BVOH", "guid": "923e604c-8432-4b09-96aa-9bbbd42207f4"},
         "cpe": {"name": "CPE", "guid": "da1872c1-b991-4795-80ad-bdac0f131726"},
         "hips": {"name": "HIPS", "guid": "a468d86a-220c-47eb-99a5-bbb47e514eb0"},
         "tpu": {"name": "TPU 95A", "guid": "19baa6a9-94ff-478b-b4a1-8157b74358d2"},
         "im-pla": {"name": "Tough", "guid": "de031137-a8ca-4a72-bd1b-17bb964033ad"}
    }
