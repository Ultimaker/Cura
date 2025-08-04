// Copyright (c) 2025 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick

import UM 1.7 as UM
import Cura 1.0 as Cura


Cura.ModeSelectorButton
{
    id: modeSelectorButton

    property string mode

    onClicked: setMode()

    function setMode()
    {
        UM.Controller.setProperty("PaintType", modeSelectorButton.mode);
    }

    function isSelected()
    {
        return UM.Controller.properties.getValue("PaintType") === modeSelectorButton.mode;
    }

    Component.onCompleted:
    {
        modeSelectorButton.selected = isSelected();
    }

    Binding
    {
        target: modeSelectorButton
        property: "selected"
        value: isSelected()
    }
}
