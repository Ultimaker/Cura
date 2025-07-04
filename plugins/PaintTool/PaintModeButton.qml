// Copyright (c) 2025 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick

import UM 1.7 as UM
import Cura 1.0 as Cura

Cura.ModeSelectorButton
{
    id: modeSelectorButton

    property string mode

    selected: base.selectedMode === modeSelectorButton.mode

    onClicked: setMode()

    function setMode()
    {
        base.selectedMode = modeSelectorButton.mode
        UM.Controller.triggerActionWithData("setPaintType", modeSelectorButton.mode)
    }
}
