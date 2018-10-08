// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.4 as UM

Item
{
    id: base
    height: UM.Theme.getSize("topheader").height
    width: UM.Theme.getSize("topheader").height

    AvatarImage
    {
        id: avatar
        width: Math.round(0.8 * parent.width)
        height: Math.round(0.8 * parent.height)
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
    }

    MouseArea
    {
        anchors.fill: avatar
        onClicked:
        {
            // Collapse/Expand the dropdown panel
            accountManagementPanel.visible = !accountManagementPanel.visible
        }
    }

    UM.PointingRectangle
    {
        id: accountManagementPanel

        width: 250
        height: 250

        anchors
        {
            top: parent.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            right: parent.right
        }

        target: Qt.point(parent.width / 2, parent.bottom)
        arrowSize: UM.Theme.getSize("default_arrow").width

        visible: false
        opacity: visible ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 100 } }

        color: UM.Theme.getColor("tool_panel_background")
        borderColor: UM.Theme.getColor("lining")
        borderWidth: UM.Theme.getSize("default_lining").width

        Loader
        {
            id: panel
            sourceComponent: login
        }
    }

    Component
    {
        id: login
        Label {text: "HOLA"}
    }
}