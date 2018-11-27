// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

Button
{
    id: base

    property var extruder

    text: catalog.i18ncp("@label %1 is filled in with the name of an extruder", "Print Selected Model with %1", "Print Selected Models with %1", UM.Selection.selectionCount).arg(extruder.name)

    checked: Cura.ExtruderManager.selectedObjectExtruders.indexOf(extruder.id) != -1
    enabled: UM.Selection.hasSelection && extruder.stack.isEnabled

    background: Item {}
    contentItem: Item
    {
        // For some reason if the extruder icon is not enclosed to the item, the size changes to fill the size of the button
        ExtruderIcon
        {
            anchors.centerIn: parent
            materialColor: model.color
            extruderEnabled: extruder.stack.isEnabled
            property int index: extruder.index
        }
    }

    onClicked:
    {
        forceActiveFocus() //First grab focus, so all the text fields are updated
        CuraActions.setExtruderForSelection(extruder.id);
    }
}
