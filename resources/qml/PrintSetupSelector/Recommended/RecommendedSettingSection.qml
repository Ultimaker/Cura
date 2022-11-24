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
    property Component content: Item { visible: false  }

    property alias enableSectionVisible: enableSectionSwitch.visible
    property alias enableSectionChecked: enableSectionSwitch.checked
    property alias enableSectionEnabled: enableSectionSwitch.enabled
    property var enableSectionClicked: { return }
    property int leftColumnWidth: width / 2

    function onEnableSectionChanged(state) {}

    height: childrenRect.height
    width: parent.width


    Item
    {
        id: sectionHeader

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
            anchors.fill: parent
            propagateComposedEvents: true
            hoverEnabled: true

            onEntered: { print("showTooltip") }
            onExited: { print("hideTooltip" ) }
        }

    }

    Loader
    {
        id: contentLoader
        width: parent.width
        height: content.height
        anchors.left: settingLabel.right
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
        sourceComponent: content
    }
}