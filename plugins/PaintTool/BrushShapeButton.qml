// Copyright (c) 2025 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick

import UM 1.7 as UM
import Cura 1.0 as Cura


UM.ToolbarButton
{
    id: buttonBrushShape

    property int shape

    checked: UM.Controller.properties.getValue("BrushShape") === buttonBrushShape.shape
    onClicked: UM.Controller.setProperty("BrushShape", buttonBrushShape.shape)
}
