// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 2.10

import UM 1.5 as UM
import Cura 1.7 as Cura


Item
{
    id: settingItem
    width: parent.width
    Layout.minimumHeight: UM.Theme.getSize("section_header").height
    Layout.fillWidth: true

    property alias settingControl: settingContainer.children
    property alias settingName: settingLabel.text
    property string tooltipText: ""
    property bool isCompressed: false

    UM.Label
    {
        id: settingLabel
        width: leftColumnWidth
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        // These numbers come from the IconWithText in RecommendedSettingSection
        anchors.leftMargin: UM.Theme.getSize("medium_button_icon").width + UM.Theme.getSize("default_margin").width
    }

    MouseArea
    {
        id: tooltipArea
        anchors.fill: settingLabel
        propagateComposedEvents: true
        hoverEnabled: true
        onEntered: base.showTooltip(parent, Qt.point(-UM.Theme.getSize("thick_margin").width, 0), tooltipText)
        onExited: base.hideTooltip()
    }

    Item
    {
        id: settingContainer
        height: childrenRect.height
        anchors.left: settingLabel.right
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
    }

    states:
    [
        State
        {
            name: "sectionClosed" // Section is hidden when the switch in parent is off
            when: isCompressed
            PropertyChanges
            {
                target: settingItem;
                opacity: 0
                height: 0
                implicitHeight: 0
                Layout.preferredHeight: 0
                Layout.minimumHeight: 0
                enabled: false // Components can still be clickable with height 0 so they need to be disabled as well.
            }
        },
        State
        {
            // All values are default. This state is only here for the animation.
            name: "sectionOpened"
            when: !isCompressed
        }
    ]

    transitions: Transition
    {
        from: "sectionOpened"; to: "sectionClosed"
        reversible: true
        ParallelAnimation
        {
            // Animate section compressing as it closes
            NumberAnimation { property: "Layout.minimumHeight"; duration: 100; }
            // Animate section dissapearring as it closes
            NumberAnimation { property: "opacity"; duration: 100; }
        }
    }
}