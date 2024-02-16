// Copyright (c) 2023 UltiMaker
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
    color: mouseArea.containsMouse || selected ? UM.Theme.getColor("background_3") : UM.Theme.getColor("background_1")

    property bool selected: false
    property string profileName: ""
    property string icon: ""
    property string custom_icon: ""
    property alias tooltipText: tooltip.text

    signal clicked()

    MouseArea
    {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        onClicked: base.clicked()
    }

    UM.ToolTip
    {
        id: tooltip
        visible: mouseArea.containsMouse
        targetPoint: Qt.point(base.x + (base.width / 2), base.y + (base.height / 2))
        width: UM.Theme.getSize("tooltip").width
    }

    Item
    {
        width: intentIcon.width
        anchors
        {
            top: parent.top
            bottom: qualityLabel.top
            horizontalCenter: parent.horizontalCenter
            topMargin: UM.Theme.getSize("narrow_margin").height
        }

        Item
        {
            id: intentIcon
            width: UM.Theme.getSize("recommended_button_icon").width
            height: UM.Theme.getSize("recommended_button_icon").height

            UM.ColorImage
            {
                anchors.fill: parent
                anchors.centerIn: parent
                visible: icon !== ""
                source: UM.Theme.getIcon(icon)
                color: UM.Theme.getColor("icon")
            }

            UM.ColorImage
            {
                anchors.fill: parent
                anchors.centerIn: parent
                visible: custom_icon !== ""
                source: custom_icon
                color: UM.Theme.getColor("icon")
            }

            Rectangle
            {
                id: circle
                anchors.fill: parent
                radius: width
                anchors.verticalCenter: parent.verticalCenter
                visible: icon === "" && custom_icon === ""
                border.width: UM.Theme.getSize("thick_lining").width
                border.color: UM.Theme.getColor("text")
                color: "transparent"

                UM.Label
                {
                    id: initialLabel
                    anchors.centerIn: parent
                    text: profileName.charAt(0).toUpperCase()
                    font: UM.Theme.getFont("small_bold")
                    horizontalAlignment: Text.AlignHCenter
                }
            }


        }
    }

    UM.Label
    {
        id: qualityLabel
        text: profileName
        anchors
        {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
            bottomMargin: UM.Theme.getSize("narrow_margin").height
        }
    }
}