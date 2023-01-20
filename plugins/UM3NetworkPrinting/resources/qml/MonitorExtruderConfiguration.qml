// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.5 as UM

import Cura 1.6 as Cura

/**
 * This component comprises a colored extruder icon, the material name, and the
 * print core name. It is used by the MonitorPrinterConfiguration component with
 * a sibling instance.
 *
 * NOTE: For most labels, a fixed height with vertical alignment is used to make
 * layouts more deterministic (like the fixed-size textboxes used in original
 * mock-ups). This is also a stand-in for CSS's 'line-height' property. Denoted
 * with '// FIXED-LINE-HEIGHT:'.
 */
Item
{
    // The material color
    property alias color: extruderIcon.materialColor

    // The extruder position
    property int position

    // The material name
    property alias material: materialLabel.text

    // The print core name (referred to as hotendID in Python)
    property alias printCore: printCoreLabel.text

    // Height is 2 x 18px labels, plus 4px spacing between them
    height: 40 * screenScaleFactor // TODO: Theme!
    width: childrenRect.width
    opacity: material != "" && material != "Empty" && position >= 0 ? 1 : 0.4

    Cura.ExtruderIcon
    {
        id: extruderIcon
        materialColor: UM.Theme.getColor("monitor_skeleton_loading")
        anchors.verticalCenter: parent.verticalCenter
    }

    Rectangle
    {
        id: materialLabelWrapper
        anchors
        {
            left: extruderIcon.right
            leftMargin: UM.Theme.getSize("default_margin").width
            verticalCenter: extruderIcon.verticalCenter
        }
        color: materialLabel.visible > 0 ? "transparent" : UM.Theme.getColor("monitor_skeleton_loading")
        height: childrenRect.height
        width: Math.max(materialLabel.contentWidth, 60 * screenScaleFactor) // TODO: Theme!
        radius: 2 * screenScaleFactor // TODO: Theme!

        UM.Label
        {
            id: materialLabel
            anchors.top: parent.top

            elide: Text.ElideRight
            text: ""
            visible: text !== ""
        }

        UM.Label
        {
            id: printCoreLabel
            anchors.top: materialLabel.bottom

            elide: Text.ElideRight
            font: UM.Theme.getFont("default_bold") // 12pt, bold
            text: ""
            visible: text !== ""
        }
    }
}
