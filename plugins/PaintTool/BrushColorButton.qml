// Copyright (c) 2025 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick

import UM 1.7 as UM
import Cura 1.0 as Cura


UM.ToolbarButton
{
    id: buttonBrushColor

    property string color

    onClicked: setColor()

    function setColor()
    {
        UM.Controller.setProperty("BrushColor", buttonBrushColor.color);
    }

    function isChecked()
    {
        return UM.Controller.properties.getValue("BrushColor") === buttonBrushColor.color;
    }

    Component.onCompleted:
    {
        buttonBrushColor.checked = isChecked();
    }

    Binding
    {
        target: buttonBrushColor
        property: "checked"
        value: isChecked()
    }
}
