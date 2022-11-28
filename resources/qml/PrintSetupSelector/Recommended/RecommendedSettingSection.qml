// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 2.10

import UM 1.6 as UM
import Cura 1.7 as Cura

Item
{
    property alias title: sectionTitle.text
    property alias icon: sectionTitle.source

    property alias enableSectionVisible: enableSectionSwitch.visible
    property alias enableSectionChecked: enableSectionSwitch.checked
    property alias enableSectionEnabled: enableSectionSwitch.enabled
    property var enableSectionClicked: { return }
    property int leftColumnWidth: Math.floor(width * 0.35)
    property var toolTipText: ""

    property alias contents: settingColumn.children

    function onEnableSectionChanged(state) {}

    height: childrenRect.height

    Item
    {
        id: sectionHeader
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.left: parent.left
        height: UM.Theme.getSize("section_header").height

        Cura.IconWithText
        {
            id: sectionTitle
            width: leftColumnWidth
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: - UM.Theme.getSize("thick_lining").width
            source: UM.Theme.getIcon("PrintQuality")
            spacing: UM.Theme.getSize("thick_margin").width
            iconSize: UM.Theme.getSize("medium_button_icon").width
            iconColor: UM.Theme.getColor("text")
            font: UM.Theme.getFont("medium_bold")
        }

        UM.Switch
        {
            id: enableSectionSwitch
            anchors.left: sectionTitle.right
            anchors.verticalCenter: parent.verticalCenter
            visible: false

            onClicked: onEnableSectionChanged(enableSectionSwitch.checked)
        }

        MouseArea
        {
            id: tooltipMouseArea
            anchors.fill: sectionTitle
            propagateComposedEvents: true
            hoverEnabled: true

            onEntered: { print("showTooltip") }
            onExited: { print("hideTooltip" ) }
        }

    }

    ColumnLayout
    {
        id: settingColumn
        width: parent.width
        height: childrenRect.height
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: sectionHeader.bottom
    }
}