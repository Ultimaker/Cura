// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: base

    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()
//    width: parent.width
    height: childrenRect.height + 2 * padding

    property Action configureSettings

    property bool settingsEnabled: Cura.ExtruderManager.activeExtruderStackId || extrudersEnabledCount.properties.value == 1
    property real padding: UM.Theme.getSize("thick_margin").width

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

//    Rectangle
//    {
//        width: parent.width - 2 * parent.padding
//        anchors
//        {
//            left: parent.left
//            right: parent.right
//            top: parent.top
//            margins: parent.padding
//        }
//        color: "blue"
//        height: 50
//    }

    Column
    {
        width: parent.width - 2 * parent.padding
        spacing: UM.Theme.getSize("default_margin").height
        anchors
        {
            left: parent.left
            right: parent.right
            top: parent.top
            margins: parent.padding
        }

        // TODO
        property real labelColumnWidth: Math.round(width / 3)
        property real settingsColumnWidth: width - labelColumnWidth

        RecommendedQualityProfileSelector
        {
            width: parent.width
            // TODO Create a reusable component with these properties to not define them separately for each component
            property real labelColumnWidth: parent.labelColumnWidth
            property real settingsColumnWidth: parent.settingsColumnWidth
        }

//        RecommendedInfillDensitySelector
//        {
//            width: parent.width
//            height: childrenRect.height
//            // TODO Create a reusable component with these properties to not define them separately for each component
//            property real labelColumnWidth: parent.labelColumnWidth
//            property real settingsColumnWidth: parent.settingsColumnWidth
//        }
//
//        RecommendedSupportSelector
//        {
//            width: parent.width
//            height: childrenRect.height
//            // TODO Create a reusable component with these properties to not define them separately for each component
//            property real labelColumnWidth: parent.labelColumnWidth
//            property real settingsColumnWidth: parent.settingsColumnWidth
//        }


//
//    // Adhesion
//    Row
//    {
//        anchors.left: parent.left
//        anchors.right: parent.right
//        height: childrenRect.height
//
//        Cura.IconWithText
//        {
//            id: adhesionHelperLabel
//            visible: adhesionCheckBox.visible
//            source: UM.Theme.getIcon("category_adhesion")
//            text: catalog.i18nc("@label", "Adhesion")
//            width: labelColumnWidth
//        }
//
//        CheckBox
//        {
//            id: adhesionCheckBox
//            property alias _hovered: adhesionMouseArea.containsMouse
//
//            //: Setting enable printing build-plate adhesion helper checkbox
//            style: UM.Theme.styles.checkbox
//            enabled: base.settingsEnabled
//
//            visible: platformAdhesionType.properties.enabled == "True"
//            checked: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none"
//
//            MouseArea
//            {
//                id: adhesionMouseArea
//                anchors.fill: parent
//                hoverEnabled: true
//                enabled: base.settingsEnabled
//                onClicked:
//                {
//                    var adhesionType = "skirt"
//                    if(!parent.checked)
//                    {
//                        // Remove the "user" setting to see if the rest of the stack prescribes a brim or a raft
//                        platformAdhesionType.removeFromContainer(0)
//                        adhesionType = platformAdhesionType.properties.value
//                        if(adhesionType == "skirt" || adhesionType == "none")
//                        {
//                            // If the rest of the stack doesn't prescribe an adhesion-type, default to a brim
//                            adhesionType = "brim"
//                        }
//                    }
//                    platformAdhesionType.setPropertyValue("value", adhesionType)
//                }
//                onEntered:
//                {
//                    base.showTooltip(adhesionCheckBox, Qt.point(-adhesionCheckBox.x, 0),
//                        catalog.i18nc("@label", "Enable printing a brim or raft. This will add a flat area around or under your object which is easy to cut off afterwards."));
//                }
//                onExited: base.hideTooltip()
//            }
//        }
//    }
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
