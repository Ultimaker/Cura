// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM


Item
{
    id: extruderInfo
    property var printCoreConfiguration

    height: childrenRect.height

    Label
    {
        id: materialLabel
        text: printCoreConfiguration.material
        elide: Text.ElideRight
        width: parent.width
        font: UM.Theme.getFont("very_small")
    }
    Label
    {
        id: printCoreLabel
        text: printCoreConfiguration.hotendID
        anchors.top: materialLabel.bottom
        elide: Text.ElideRight
        width: parent.width
        font: UM.Theme.getFont("very_small")
        opacity: 0.5
    }
}
