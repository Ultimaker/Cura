// Copyright (c) 2020 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.1 as UM

ScrollView
{
    clip: true

    // Setting this property to false hides the scrollbar both when the scrollbar is not needed (child height < height)
    // and when the scrollbar is not actively being hovered or pressed
    property bool scrollAlwaysVisible: true

    ScrollBar.vertical: ScrollBar
    {
        hoverEnabled: true
        policy: parent.scrollAlwaysVisible ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.bottom: parent.bottom

        contentItem: Rectangle
        {
            implicitWidth: UM.Theme.getSize("scrollbar").width
            opacity: (parent.active || parent.parent.scrollAlwaysVisible) ? 1.0 : 0.0
            radius: Math.round(width / 2)
            color:
            {
                if (parent.pressed)
                {
                    return UM.Theme.getColor("scrollbar_handle_down")
                }
                else if (parent.hovered)
                {
                    return UM.Theme.getColor("scrollbar_handle_hover")
                }
                return UM.Theme.getColor("scrollbar_handle")
            }
            Behavior on color { ColorAnimation { duration: 100; } }
            Behavior on opacity { NumberAnimation { duration: 100 } }
        }
    }
}