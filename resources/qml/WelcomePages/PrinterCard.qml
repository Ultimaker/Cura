// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.1 as Cura

Control
{
    id: root
    property alias text: link_text.text
    property alias imageSource: image.source
    property var onClicked

    states:
    [
        State
        {
            name: "hovered";
            when: mouse_area.containsMouse
            PropertyChanges
            {
                target: background
                color: UM.Theme.getColor("monitor_card_hover")
            }
            PropertyChanges
            {
                target: link_text
                font.underline: true
            }
        }
    ]

    MouseArea
    {
        id: mouse_area
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.onClicked && root.onClicked()
    }

    rightPadding: UM.Theme.getSize("wide_margin").width
    bottomPadding: UM.Theme.getSize("wide_margin").height
    leftPadding: UM.Theme.getSize("wide_margin").width

    background: Rectangle
    {
        id: background
        height: parent.height
        border.color: UM.Theme.getColor("primary_button")
        color: "transparent"
        border.width: 1
        radius: 3
    }

    contentItem: ColumnLayout
    {
        id: column
        spacing: UM.Theme.getSize("wide_margin").height
        height: childrenRect.height
        width: childrenRect.width

        Image
        {
            id: image
            source: imageSource
            width: 180 * screenScaleFactor
            sourceSize.width: width
            sourceSize.height: height
        }

        UM.Label
        {
            id: link_text
            Layout.fillWidth: true
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("text_link")
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
