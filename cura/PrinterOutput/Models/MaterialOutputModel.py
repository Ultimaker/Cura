# Copyright (c) 2017 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional

from PyQt6.QtCore import pyqtProperty, QObject


class MaterialOutputModel(QObject):
    def __init__(self, guid: Optional[str], type: str, color: str, brand: str, name: str, parent = None) -> None:
        super().__init__(parent)

        name, guid = MaterialOutputModel.getMaterialFromDefinition(guid, type, brand, name)
        self._guid = guid
        self._type = type
        self._color = color
        self._brand = brand
        self._name = name

    @pyqtProperty(str, constant = True)
    def guid(self) -> str:
        return self._guid if self._guid else ""

    @staticmethod
    def getMaterialFromDefinition(guid, type, brand, name):

        _MATERIAL_MAP = {	"abs-cf10"  :{"name": "ABS-CF"        ,"guid": "495a0ce5-9daf-4a16-b7b2-06856d82394d"},
                            "abs-wss1"  :{"name" :"ABS-R"         ,"guid": "88c8919c-6a09-471a-b7b6-e801263d862d"},
                            "asa"       :{"name" :"ASA"           ,"guid": "f79bc612-21eb-482e-ad6c-87d75bdde066"},
                            "nylon12-cf":{"name": "Nylon 12 CF"   ,"guid": "3c6f2877-71cc-4760-84e6-4b89ab243e3b"},
                            "wss1"      :{"name" :"RapidRinse"    ,"guid": "a140ef8f-4f26-4e73-abe0-cfc29d6d1024"},
                            "sr30"      :{"name" :"SR-30"         ,"guid": "77873465-83a9-4283-bc44-4e542b8eb3eb"}
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
