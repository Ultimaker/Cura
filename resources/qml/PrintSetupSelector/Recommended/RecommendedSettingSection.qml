// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 2.10

import UM 1.7 as UM
import Cura 1.7 as Cura

Item
{
    id: settingSection
    property alias title: sectionTitle.text
    property alias icon: sectionTitle.source

    property alias enableSectionSwitchVisible: enableSectionSwitch.visible
    property alias enableSectionSwitchChecked: enableSectionSwitch.checked
    property alias enableSectionSwitchEnabled: enableSectionSwitch.enabled
    property string tooltipText: ""
    property var enableSectionClicked: { return }
    property int leftColumnWidth: Math.floor(width * 0.35)
    property bool isCompressed: false

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
            source: UM.Theme.getIcon("PrintQuality")
            spacing: UM.Theme.getSize("default_margin").width
            iconSize: UM.Theme.getSize("medium_button_icon").width
            iconColor: UM.Theme.getColor("text")
            font: UM.Theme.getFont("medium_bold")
        }

        MouseArea
        {
            id: tooltipArea
            anchors.fill: sectionTitle
            propagateComposedEvents: true
            hoverEnabled: true
            onEntered: base.showTooltip(parent, Qt.point(-UM.Theme.getSize("thick_margin").width, 0), tooltipText)
            onExited: base.hideTooltip()
        }

    }

    UM.Switch
    {
        id: enableSectionSwitch
        anchors.left: parent.left
        // These numbers come from the IconWithText in RecommendedSettingSection.
        anchors.leftMargin: leftColumnWidth + UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width
        anchors.verticalCenter: sectionHeader.verticalCenter
        visible: false

        // This delay forces the setting change to happen after the setting section open/close animation. This is so the animation is smooth.
        Timer
        {
            id: updateTimer
            interval: 500 // This interval is set long enough so you can spam click the button on/off without lag.
            repeat: false
            onTriggered: onEnableSectionChanged(enableSectionSwitch.checked)
        }
        onClicked: updateTimer.restart()
    }

    ColumnLayout
    {
        id: settingColumn
        width: parent.width
        spacing: UM.Theme.getSize("thin_margin").height
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: sectionHeader.bottom
        anchors.topMargin: UM.Theme.getSize("narrow_margin").height
    }

    states:
    [
        State
        {
            name: "settingListClosed"
            when: !enableSectionSwitchChecked && enableSectionSwitchEnabled
            PropertyChanges
            {
                target: settingSection
                isCompressed: true
                implicitHeight: 0
            }
            PropertyChanges
            {
                target: settingColumn
                spacing: 0
            }
        },
        State
        {
            // Use default properties. This is only here for the animation. 
            name: "settingListOpened"
            when: enableSectionSwitchChecked && enableSectionSwitchEnabled
        }
    ]

    // Animate section closing
    transitions: Transition
    {
        from: "settingListOpened"; to: "settingListClosed"
        reversible: true
        // Animate section compressing as it closes
        NumberAnimation { property: "implicitHeight"; duration: 100; }
    }
}