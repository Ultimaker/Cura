# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from PyQt6.QtCore import pyqtProperty, QObject


class MaterialOutputModel(QObject):
    def __init__(self, guid: Optional[str], type: str, color: str, brand: str, name: str, parent = None) -> None:
        super().__init__(parent)

        name, guid = MaterialOutputModel.getMaterialFromDefinition(guid,type, brand, name)
        self._guid =guid
        self._type = type
        self._color = color
        self._brand = brand
        self._name = name

    @pyqtProperty(str, constant = True)
    def guid(self) -> str:
        return self._guid if self._guid else ""

    @staticmethod
    def getMaterialFromDefinition(guid, type, brand, name):

        _MATERIAL_MAP = {	"abs" 		:{"name" :"abs_175"       ,"guid": "2780b345-577b-4a24-a2c5-12e6aad3e690"},
                            "abs-wss1"	:{"name" :"absr_175"      ,"guid": "88c8919c-6a09-471a-b7b6-e801263d862d"},
                            "asa" 		:{"name" :"asa_175"       ,"guid": "416eead4-0d8e-4f0b-8bfc-a91a519befa5"},
                            "nylon-cf" 	:{"name" :"cffpa_175"     ,"guid": "85bbae0e-938d-46fb-989f-c9b3689dc4f0"},
                            "nylon"		:{"name" :"nylon_175"     ,"guid": "283d439a-3490-4481-920c-c51d8cdecf9c"},
                            "pc"		:{"name" :"pc_175"        ,"guid": "62414577-94d1-490d-b1e4-7ef3ec40db02"},
                            "petg"		:{"name" :"petg_175"      ,"guid": "69386c85-5b6c-421a-bec5-aeb1fb33f060"},
                            "pla" 		:{"name" :"pla_175"       ,"guid": "0ff92885-617b-4144-a03c-9989872454bc"},
                            "pva"		:{"name" :"pva_175"       ,"guid": "a4255da2-cb2a-4042-be49-4a83957a2f9a"},
                            "wss1"		:{"name" :"rapidrinse_175","guid": "a140ef8f-4f26-4e73-abe0-cfc29d6d1024"},
                            "sr30"		:{"name" :"sr30_175"      ,"guid": "77873465-83a9-4283-bc44-4e542b8eb3eb"},
                            "im-pla"    :{"name" :"tough_pla_175" ,"guid": "96fca5d9-0371-4516-9e96-8e8182677f3c"},
                            "bvoh"		:{"name" :"bvoh_175"      ,"guid": "923e604c-8432-4b09-96aa-9bbbd42207f4"},
                            "cpe"		:{"name" :"cpe_175"       ,"guid": "da1872c1-b991-4795-80ad-bdac0f131726"},
                            "hips"		:{"name" :"hips_175"      ,"guid": "a468d86a-220c-47eb-99a5-bbb47e514eb0"},
                            "tpu"		:{"name" :"tpu_175"       ,"guid": "19baa6a9-94ff-478b-b4a1-8157b74358d2"}
                        }


        if guid is None and brand != "empty" and type in _MATERIAL_MAP:
            name = _MATERIAL_MAP[type]["name"]
            guid = _MATERIAL_MAP[type]["guid"]
        return name, guid


    @pyqtProperty(str, constant = True)
    def type(self) -> str:
        return self._type

    @pyqtProperty(str, constant = True)
    def brand(self) -> str:
        return self._brand

    @pyqtProperty(str, constant = True)
    def color(self) -> str:
        return self._color

    @pyqtProperty(str, constant = True)
    def name(self) -> str:
        return self._name

    def __eq__(self, other):
        if self is other:
            return True
        if type(other) is not MaterialOutputModel:
            return False

        return self.guid == other.guid and self.type == other.type and self.brand == other.brand and self.color == other.color and self.name == other.name
