// Copyright (c) 2019 Ultimaker B.V.
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
        color: UM.Theme.getColor("monitor_skeleton_loading")
        position: 0
    }

    Rectangle
    {
        id: materialLabelWrapper
        anchors
        {
            left: extruderIcon.right
            leftMargin: 12 * screenScaleFactor // TODO: Theme!
        }
        color: materialLabel.visible > 0 ? "transparent" : UM.Theme.getColor("monitor_skeleton_loading")
        height: 18 * screenScaleFactor // TODO: Theme!
        width: Math.max(materialLabel.contentWidth, 60 * screenScaleFactor) // TODO: Theme!
        radius: 2 * screenScaleFactor // TODO: Theme!

        Label
        {
            id: materialLabel

            color: UM.Theme.getColor("monitor_text_primary")
            elide: Text.ElideRight
            font: UM.Theme.getFont("default") // 12pt, regular
            text: ""
            visible: text !== ""

            // FIXED-LINE-HEIGHT:
            height: parent.height
            verticalAlignment: Text.AlignVCenter
            renderType: Text.NativeRendering
        }
    }

    Rectangle
    {
        id: printCoreLabelWrapper
        anchors
        {
            left: materialLabelWrapper.left
            bottom: parent.bottom
        }
        color: printCoreLabel.visible > 0 ? "transparent" : UM.Theme.getColor("monitor_skeleton_loading")
        height: 18 * screenScaleFactor // TODO: Theme!
        width: Math.max(printCoreLabel.contentWidth, 36 * screenScaleFactor) // TODO: Theme!
        radius: 2 * screenScaleFactor // TODO: Theme!

        Label
        {
            id: printCoreLabel

            color: UM.Theme.getColor("monitor_text_primary")
            elide: Text.ElideRight
            font: UM.Theme.getFont("default_bold") // 12pt, bold
            text: ""
            visible: text !== ""

            // FIXED-LINE-HEIGHT:
            height: parent.height
            verticalAlignment: Text.AlignVCenter
            renderType: Text.NativeRendering
        }
    }
}
