// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 2.0
import UM 1.3 as UM

/**
 * A MonitorInfoBlurb is an extension of the GenericPopUp used to show static information (vs. interactive context
 * menus). It accepts some text (text), an item to link to to (target), and a specification of which side of the target
 * to appear on (direction). It also sets the GenericPopUp's color to black, to differentiate itself from a menu.
 */
Item
{
    property alias text: innerLabel.text
    property alias target: popUp.target
    property alias direction: popUp.direction

    GenericPopUp
    {
        id: popUp

        // Which way should the pop-up point? Default is up, but will flip when required
        direction: "up"

        // Use dark grey for info blurbs and white for context menus
        color: UM.Theme.getColor("monitor_tooltip")

        contentItem: Item
        {
            id: contentWrapper
            implicitWidth: childrenRect.width
            implicitHeight: innerLabel.contentHeight + 2 * innerLabel.padding
            Label
            {
                id: innerLabel
                padding: 12 * screenScaleFactor // TODO: Theme!
                text: ""
                wrapMode: Text.WordWrap
                width: 240 * screenScaleFactor // TODO: Theme!
                color: UM.Theme.getColor("monitor_tooltip_text")
                font: UM.Theme.getFont("default")
                renderType: Text.NativeRendering
            }
        }
    }

    function open() {
        popUp.open()
    }
    function close() {
        popUp.close()
    }
}
