// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 2.10

import UM 1.5 as UM
import Cura 1.7 as Cura


Rectangle
{
    id: base
    height: 60
    Layout.fillWidth: true
    color: mouseArea.containsMouse || selected ? UM.Theme.getColor("um_blue_1") : UM.Theme.getColor("background_1")

    property alias iconSource: intentIcon.source
    property alias text: qualityLabel.text
    property bool selected: false

    signal clicked()

    MouseArea
    {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: base.clicked()
    }

    Item
    {
        width: intentIcon.width
        anchors
        {
            top: parent.top
            bottom: qualityLabel.top
            horizontalCenter: parent.horizontalCenter
        }

        UM.ColorImage
        {
            id: intentIcon
            width: UM.Theme.getSize("recommended_button_icon").width
            height: width
            anchors.centerIn: parent
            color: UM.Theme.getColor("icon")
        }
    }

    UM.Label
    {
        id: qualityLabel
        anchors
        {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            bottomMargin: UM.Theme.getSize("narrow_margin").height
        }
    }
}