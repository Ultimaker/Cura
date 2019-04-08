// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.4 as UM


//
// A notification icon which is a circle with a number at the center, that can be used to indicate, for example, how
// many new messages that are available.
//
Rectangle
{
    id: notificationIcon
    color: UM.Theme.getColor("notification_icon")
    width: UM.Theme.getSize("notification_icon").width
    height: UM.Theme.getSize("notification_icon").height
    radius: (0.5 * width) | 0

    property alias labelText: notificationLabel.text
    property alias labelFont: notificationLabel.font

    Label
    {
        id: notificationLabel
        anchors.fill: parent
        color: UM.Theme.getColor("primary_text")
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        font: UM.Theme.getFont("default")
        renderType: Text.NativeRendering

        // This is a bit of a hack, but we don't really have enough room for 2 characters (eg 9+). The default font
        // does have a tad bit to much spacing. So instead of adding a whole new font, we just modify it a bit for this
        // specific instance.
        Component.onCompleted: font.letterSpacing = -1
    }
}
