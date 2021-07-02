// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

/**
 * This component is a sort of "super icon" which includes a colored SVG image
 * as well as the extruder position number. It is used in the the
 * MonitorExtruderConfiguration component.
 */
Item
{
    // The material color
    property alias color: icon.color

    // The extruder position; NOTE: Decent human beings count from 0
    property int position: 0

    // The extruder icon size; NOTE: This shouldn't need to be changed
    property int size: 32 * screenScaleFactor // TODO: Theme!

    // THe extruder icon source; NOTE: This shouldn't need to be changed
    property string iconSource: "../svg/icons/Extruder.svg"

    height: size
    width: size

    UM.RecolorImage
    {
        id: icon
        anchors.fill: parent
        source: iconSource
        width: size
    }

    Label
    {
        id: positionLabel
        anchors.centerIn: icon
        font: UM.Theme.getFont("small")
        color: UM.Theme.getColor("text")
        height: Math.round(size / 2)
        horizontalAlignment: Text.AlignHCenter
        text: position + 1
        verticalAlignment: Text.AlignVCenter
        width: Math.round(size / 2)
        visible: position >= 0
        renderType: Text.NativeRendering
    }
}
