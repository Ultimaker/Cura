// Copyright (c) 2025 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick

import UM 1.7 as UM
import Cura 1.0 as Cura


UM.ToolbarButton
{
    id: buttonBrushColor

    property string color

    checked: base.selectedColor === buttonBrushColor.color

    onClicked: setColor()

    function setColor()
    {
        base.selectedColor = buttonBrushColor.color
        UM.Controller.triggerActionWithData("setBrushColor", buttonBrushColor.color)
    }
}
