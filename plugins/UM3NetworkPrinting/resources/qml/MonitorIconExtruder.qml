// Copyright (c) 2018 Ultimaker B.V.
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
    property int size: 32 // TODO: Theme!

    // THe extruder icon source; NOTE: This shouldn't need to be changed
    property string iconSource: "../svg/icons/extruder.svg"

    height: size
    width: size

    UM.RecolorImage
    {
        id: icon
        anchors.fill: parent
        source: iconSource
        width: size
    }

    /*
     * The label uses some "fancy" math to ensure that if you change the overall
     * icon size, the number scales with it. That is to say, the font properties
     * are linked to the icon size, NOT the theme. And that's intentional.
     */
    Label
    {
        id: positionLabel
        font
        {
            pointSize: Math.round(size * 0.3125)
            weight: Font.Bold
        }
        height: Math.round(size / 2) * screenScaleFactor
        horizontalAlignment: Text.AlignHCenter
        text: position + 1
        verticalAlignment: Text.AlignVCenter
        width: Math.round(size / 2) * screenScaleFactor
        x: Math.round(size * 0.25) * screenScaleFactor
        y: Math.round(size * 0.15625) * screenScaleFactor
        // TODO: Once 'size' is themed, screenScaleFactor won't be needed
    }
}