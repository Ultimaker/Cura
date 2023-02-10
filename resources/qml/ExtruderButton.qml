// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.ToolbarButton
{
    id: base

    property var extruder
    property var extruderNumberFont: UM.Theme.getFont("small_emphasis")

    toolItem: ExtruderIcon
    {
        materialColor: extruder.color
        extruderEnabled: extruder.stack.isEnabled
        iconVariant: "default"
        font: extruderNumberFont
        property int index: extruder.index
    }
}
