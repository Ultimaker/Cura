// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura


//
//  Adhesion
//
Item
{
    id: enableAdhesionRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)

    Cura.IconWithText
    {
        id: enableAdhesionRowTitle
        anchors.top: parent.top
        anchors.left: parent.left
        source: UM.Theme.getIcon("category_adhesion")
        text: catalog.i18nc("@label", "Adhesion")
        font: UM.Theme.getFont("medium")
        width: labelColumnWidth
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

        CheckBox
        {
            id: enableAdhesionCheckBox
            anchors.verticalCenter: parent.verticalCenter

            property alias _hovered: adhesionMouseArea.containsMouse

            //: Setting enable printing build-plate adhesion helper checkbox
            style: UM.Theme.styles.checkbox
            enabled: recommendedPrintSetup.settingsEnabled

            visible: platformAdhesionType.properties.enabled == "True"
            checked: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none"

            MouseArea
            {
                id: adhesionMouseArea
                anchors.fill: parent
                hoverEnabled: true

                onClicked:
                {
                    var adhesionType = "skirt"
                    if (!parent.checked)
                    {
                        // Remove the "user" setting to see if the rest of the stack prescribes a brim or a raft
                        platformAdhesionType.removeFromContainer(0)
                        adhesionType = platformAdhesionType.properties.value
                        if(adhesionType == "skirt" || adhesionType == "none")
                        {
                            // If the rest of the stack doesn't prescribe an adhesion-type, default to a brim
                            adhesionType = "brim"
                        }
                    }
                    platformAdhesionType.setPropertyValue("value", adhesionType)
                }

                onEntered:
                {
                    base.showTooltip(enableAdhesionCheckBox, Qt.point(-enableAdhesionContainer.x - UM.Theme.getSize("thick_margin").width, 0),
                        catalog.i18nc("@label", "Enable printing a brim or raft. This will add a flat area around or under your object which is easy to cut off afterwards."));
                }
                onExited: base.hideTooltip()
            }
        }
    }

    UM.SettingPropertyProvider
    {
        id: platformAdhesionType
        containerStack: Cura.MachineManager.activeMachine
        removeUnusedValue: false //Doesn't work with settings that are resolved.
        key: "adhesion_type"
        watchedProperties: [ "value", "enabled" ]
        storeIndex: 0
    }
}