// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

Cura.ToolbarButton
{
    id: base

    property var extruder

    text: catalog.i18ncp("@label %1 is filled in with the name of an extruder", "Print Selected Model with %1", "Print Selected Models with %1", UM.Selection.selectionCount).arg(extruder.name)

    checked: Cura.ExtruderManager.selectedObjectExtruders.indexOf(extruder.id) != -1
    enabled: UM.Selection.hasSelection && extruder.stack.isEnabled

    toolItem: ExtruderIcon
    {
        materialColor: extruder.color
        extruderEnabled: extruder.stack.isEnabled
        iconVariant: "default"
        property int index: extruder.index
    }

    onClicked:
    {
        forceActiveFocus() //First grab focus, so all the text fields are updated
        CuraActions.setExtruderForSelection(extruder.id)
    }
}
