// Copyright (c) 2019 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.1 as UM

ScrollView
{
    clip: true
    property bool scrollAlwaysVisible: false

    ScrollBar.vertical: ScrollBar
    {
        id: control
        hoverEnabled: true
        policy: parent.scrollAlwaysVisible ? ScrollBar.AlwaysOn : ScrollBar.AsNeeded
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.bottom: parent.bottom

        contentItem: Rectangle
        {
            implicitWidth: UM.Theme.getSize("scrollbar").width
            opacity: (control.active || control.policy == ScrollBar.AlwaysOn) ? 1.0 : 0.0
            radius: Math.round(width / 2)
            color: control.pressed ? UM.Theme.getColor("scrollbar_handle_down") : control.hovered ? UM.Theme.getColor("scrollbar_handle_hover") : UM.Theme.getColor("scrollbar_handle")
            Behavior on color { ColorAnimation { duration: 100; } }
            Behavior on opacity { NumberAnimation { duration: 100 } }
        }
    }
}