// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

/**
 * This component comprises a buildplate icon and the buildplate name. It is
 * used by the MonitorPrinterConfiguration component along with two instances
 * of MonitorExtruderConfiguration.
 *
 * NOTE: For most labels, a fixed height with vertical alignment is used to make
 * layouts more deterministic (like the fixed-size textboxes used in original
 * mock-ups). This is also a stand-in for CSS's 'line-height' property. Denoted
 * with '// FIXED-LINE-HEIGHT:'.
 */
Item
{
    // The buildplate name
    property alias buildplate: buildplateLabel.text

    // Height is one 18px label/icon
    height: 18 * screenScaleFactor // TODO: Theme!
    width: childrenRect.width

    Row
    {
        height: parent.height
        spacing: 12 * screenScaleFactor // TODO: Theme! (Should be same as extruder spacing)

        // This wrapper ensures that the buildplate icon is located centered
        // below an extruder icon.
        Item
        {
            height: parent.height
            width: 32 * screenScaleFactor // TODO: Theme! (Should be same as extruder icon width)

            UM.RecolorImage
            {
                id: buildplateIcon
                anchors.centerIn: parent
                color: "#0a0850" // TODO: Theme! (Standard purple)
                height: parent.height
                source: "../svg/icons/buildplate.svg"
                width: height
            }
        }
        
        Label
        {
            id: buildplateLabel
            color: "#191919" // TODO: Theme!
            elide: Text.ElideRight
            font: UM.Theme.getFont("very_small") // 12pt, regular
            text: ""

            // FIXED-LINE-HEIGHT:
            height: 18 * screenScaleFactor // TODO: Theme!
            verticalAlignment: Text.AlignVCenter
        }
    }
}