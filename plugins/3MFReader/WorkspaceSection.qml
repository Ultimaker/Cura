// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.2

import UM 1.5 as UM
import Cura 1.1 as Cura


Item
{
    property alias title: sectionTitle.text
    property alias iconSource: sectionTitleIcon.source
    property Component content: Item { visible: false  }

    property alias comboboxTitle: comboboxLabel.text
    property Component combobox: Item { visible: false }
    property var comboboxTooltipText: ""
    property var comboboxVisible: false



    width: parent.width
    height: childrenRect.height
    anchors.leftMargin: UM.Theme.getSize("default_margin").width

    UM.TooltipArea
    {
        id: comboboxTooltip
        width: (parent.width / 3) | 0
        height: visible ? UM.Theme.getSize("default_margin").height : 0
        anchors.top: parent.top
        anchors.right: parent.right
        visible: combobox.visible
        text: comboboxTooltipText

        UM.Label
        {
            id: comboboxLabel
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.bottomMargin: UM.Theme.getSize("default_margin").height
            visible: combobox.visible
            text: ""
            font: UM.Theme.getFont("default_bold")
        }

        Loader
        {
            id: comboboxLoader
            width: parent.width
            height: UM.Theme.getSize("button").height
            anchors.top: comboboxLabel.bottom
            anchors.left: parent.left
            sourceComponent: combobox
        }
    }

    Row
    {
        id: sectionTitleRow
        anchors.top: parent.top
        anchors.bottomMargin: UM.Theme.getSize("default_margin").height
        spacing: UM.Theme.getSize("default_margin").width

        UM.ColorImage
        {
            id: sectionTitleIcon
            anchors.verticalCenter: parent.verticalCenter
            source: ""
            height: UM.Theme.getSize("medium_button_icon").height
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