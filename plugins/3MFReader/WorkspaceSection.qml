// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3


import UM 1.5 as UM


Item
{
    property alias title: sectionTitle.text
    property alias iconSource: sectionTitleIcon.source
    property Component content: Item { visible: false  }

    property alias comboboxTitle: comboboxLabel.text
    property Component combobox: Item { visible: false }
    property string comboboxTooltipText: ""
    property bool comboboxVisible: false

    width: parent.width
    height: childrenRect.height
    anchors.leftMargin: UM.Theme.getSize("default_margin").width

    Row
    {
        id: sectionTitleRow
        anchors.top: parent.top
        bottomPadding: UM.Theme.getSize("default_margin").height
        spacing: UM.Theme.getSize("default_margin").width

        UM.ColorImage
        {
            id: sectionTitleIcon
            anchors.verticalCenter: parent.verticalCenter
            source: ""
            height: UM.Theme.getSize("medium_button_icon").height
            color: UM.Theme.getColor("text")
            width: height
        }
        UM.Label
        {
            id: sectionTitle
            text: ""
            anchors.verticalCenter: parent.verticalCenter
            font: UM.Theme.getFont("default_bold")
        }
    }

    Item
    {
        id: comboboxTooltip
        width: Math.round(parent.width / 2.5)
        height: visible ? UM.Theme.getSize("default_margin").height : 0
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        visible: comboboxVisible

        UM.Label
        {
            id: comboboxLabel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            visible: comboboxVisible && text != ""
            text: ""
            font: UM.Theme.getFont("default_bold")
        }

        Loader
        {
            id: comboboxLoader
            width: parent.width
            height: UM.Theme.getSize("button").height
            anchors.top: comboboxLabel.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            sourceComponent: combobox
        }

        MouseArea
        {
            id: helpIconMouseArea
            anchors.right: parent.right
            anchors.verticalCenter: comboboxLabel.verticalCenter
            width: childrenRect.width
            height: childrenRect.height
            hoverEnabled: true

            UM.ColorImage
            {
                width: UM.Theme.getSize("section_icon").width
                height: width

                visible: comboboxTooltipText != ""
                source: UM.Theme.getIcon("Help")
                color: UM.Theme.getColor("text")

                UM.ToolTip
                {
                    text: comboboxTooltipText
                    visible: helpIconMouseArea.containsMouse
                    targetPoint: Qt.point(parent.x + Math.round(parent.width / 2), parent.y)
                    x: 0
                    y: parent.y + parent.height + UM.Theme.getSize("default_margin").height
                    width: UM.Theme.getSize("tooltip").width
                }
            }
        }
    }


    Loader
    {
        width: parent.width
        height: content.height
        anchors.top: sectionTitleRow.bottom
        sourceComponent: content
    }

    function reloadValues()
    {
        comboboxLoader.sourceComponent = null
        comboboxLoader.sourceComponent = combobox
    }
}