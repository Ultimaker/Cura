// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura

Button
{
    id: base

    property alias iconSource: applicationIcon.source
    property alias displayName: applicationDisplayName.text
    property alias tooltipText: tooltip.text
    property bool isExternalLink: false
    property color borderColor: hovered ? UM.Theme.getColor("primary") : "transparent"
    property color backgroundColor: hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")
    Behavior on backgroundColor { ColorAnimation { duration: 200; } }
    Behavior on borderColor { ColorAnimation { duration: 200; } }

    hoverEnabled: true
    width: UM.Theme.getSize("application_switcher_item").width
    height: UM.Theme.getSize("application_switcher_item").height

    background: Rectangle
    {
        color:backgroundColor
        border.color: borderColor
        border.width: UM.Theme.getSize("default_lining").width
    }

    UM.ToolTip
    {
        id: tooltip
        tooltipText: base.text
        visible: base.hovered
    }

    Column
    {
        id: applicationButtonContent
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter

        UM.ColorImage
        {
            id: applicationIcon
            anchors.horizontalCenter: parent.horizontalCenter

            color: UM.Theme.getColor("icon")
            width: UM.Theme.getSize("application_switcher_icon").width
            height: width

            UM.ColorImage
            {
                id: externalLinkIndicatorIcon
                visible: base.isExternalLink

                anchors
                {
                    bottom: parent.bottom
                    bottomMargin: - Math.round(height * 1 / 6)
                    right: parent.right
                    rightMargin: - Math.round(width * 5 / 6)
                }
                width: UM.Theme.getSize("icon_indicator").width
                height: width
                color: UM.Theme.getColor("icon")
                source: UM.Theme.getIcon("LinkExternal")
            }
        }

        UM.Label
        {
            id: applicationDisplayName

            anchors.left: parent.left
            anchors.right: parent.right

            height: base.height - applicationIcon.height - 2 * UM.Theme.getSize("default_margin").width  // Account for the top and bottom margins
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
    }
}
