// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

/**
 * This component comprises a colored extruder icon, the material name, and the
 * print core name. It is used by the MonitorPrinterConfiguration component with
 * a sibling instance as well as a MonitorBuildplateConfiguration instance.
 *
 * NOTE: For most labels, a fixed height with vertical alignment is used to make
 * layouts more deterministic (like the fixed-size textboxes used in original
 * mock-ups). This is also a stand-in for CSS's 'line-height' property. Denoted
 * with '// FIXED-LINE-HEIGHT:'.
 */
Item
{
    // The material color
    property alias color: extruderIcon.color

    // The extruder position; NOTE: Decent human beings count from 0
    property alias position: extruderIcon.position

    // The material name
    property alias material: materialLabel.text

    // The print core name (referred to as hotendID in Python)
    property alias printCore: printCoreLabel.text

    // Height is 2 x 18px labels, plus 4px spacing between them
    height: 40 * screenScaleFactor // TODO: Theme!
    width: childrenRect.width

    MonitorIconExtruder
    {
        id: extruderIcon
        color: "#eeeeee" // TODO: Theme!
        position: 0
    }
    Label
    {
        id: materialLabel
        anchors
        {
            left: extruderIcon.right
            leftMargin: 12 * screenScaleFactor // TODO: Theme!
        }
        color: "#191919" // TODO: Theme!
        elide: Text.ElideRight
        font: UM.Theme.getFont("default") // 12pt, regular
        text: ""

        // FIXED-LINE-HEIGHT:
        height: 18 * screenScaleFactor // TODO: Theme!
        verticalAlignment: Text.AlignVCenter
    }
    Label
    {
        id: printCoreLabel
        anchors
        {
            left: materialLabel.left
            bottom: parent.bottom
        }
        color: "#191919" // TODO: Theme!
        elide: Text.ElideRight
        font: UM.Theme.getFont("default_bold") // 12pt, bold
        text: ""

        // FIXED-LINE-HEIGHT:
        height: 18 * screenScaleFactor // TODO: Theme!
        verticalAlignment: Text.AlignVCenter
    }
}