// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7

import UM 1.5 as UM
import Cura 1.0 as Cura


//
//  Adhesion
//
Item
{
    id: enableAdhesionRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)
    property var curaRecommendedMode: Cura.RecommendedMode {}

    Cura.IconWithText
    {
        id: enableAdhesionRowTitle
        anchors.top: parent.top
        anchors.left: parent.left
        source: UM.Theme.getIcon("Adhesion")
        text: catalog.i18nc("@label", "Adhesion")
        font: UM.Theme.getFont("medium")
        width: labelColumnWidth
        iconSize: UM.Theme.getSize("medium_button_icon").width
    }

    Item
    {
        id: enableAdhesionContainer
        height: enableAdhesionCheckBox.height

        anchors
        {
            left: enableAdhesionRowTitle.right
            right: parent.right
            verticalCenter: enableAdhesionRowTitle.verticalCenter
        }

        UM.CheckBox
        {
            id: enableAdhesionCheckBox
            anchors.verticalCenter: parent.verticalCenter

            //: Setting enable printing build-plate adhesion helper checkbox
            enabled: recommendedPrintSetup.settingsEnabled

            visible: platformAdhesionType.properties.enabled == "True"
            checked: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none"

            MouseArea
            {
                id: adhesionMouseArea
                anchors.fill: parent
                hoverEnabled: true
                // propagateComposedEvents used on adhesionTooltipMouseArea does not work with Controls Components.
                // It only works with other MouseAreas, so this is required
                onClicked: curaRecommendedMode.setAdhesion(!parent.checked)
            }
        }
    }

    MouseArea
    {
        id: adhesionTooltipMouseArea
        anchors.fill: parent
        propagateComposedEvents: true
        hoverEnabled: true

        onEntered:base.showTooltip(enableAdhesionCheckBox, Qt.point(-enableAdhesionContainer.x - UM.Theme.getSize("thick_margin").width, 0),
                catalog.i18nc("@label", "Enable printing a brim or raft. This will add a flat area around or under your object which is easy to cut off afterwards."));
        onExited: base.hideTooltip()
    }

    UM.SettingPropertyProvider
    {
        id: platformAdhesionType
        containerStack: Cura.MachineManager.activeMachine
        removeUnusedValue: false //Doesn't work with settings that are resolved.
        key: "adhesion_type"
        watchedProperties: [ "value", "resolve", "enabled" ]
        storeIndex: 0
    }
}
