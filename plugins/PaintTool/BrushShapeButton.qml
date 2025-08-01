// Copyright (c) 2025 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick

import UM 1.7 as UM
import Cura 1.0 as Cura


UM.ToolbarButton
{
    id: buttonBrushShape

    property int shape

    onClicked: setShape()

    function setShape()
    {
        UM.Controller.setProperty("BrushShape", buttonBrushShape.shape)
    }

    function isChecked()
    {
        return UM.Controller.properties.getValue("BrushShape") === buttonBrushShape.shape;
    }

    Component.onCompleted:
    {
        buttonBrushShape.checked = isChecked();
    }

    Binding
    {
        target: buttonBrushShape
        property: "checked"
        value: isChecked()
    }
}
