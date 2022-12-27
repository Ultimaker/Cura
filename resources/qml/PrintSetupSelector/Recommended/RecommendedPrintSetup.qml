// Copyright (c) 2022 UltiMaker
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura
import ".."

ScrollView
{
    id: recommendedPrintSetup

    implicitHeight: settingsColumn.height + 2 * padding

    property bool settingsEnabled: Cura.ExtruderManager.activeExtruderStackId || extrudersEnabledCount.properties.value == 1

    padding: UM.Theme.getSize("default_margin").width

    function onModeChanged() {}

    ScrollBar.vertical: UM.ScrollBar {
        id: scroll
        anchors
        {
            top: parent.top
            right: parent.right
            bottom: parent.bottom
        }
    }

    Column
    {
        id: settingsColumn
        spacing: UM.Theme.getSize("default_margin").height

        width: recommendedPrintSetup.width - 2 * recommendedPrintSetup.padding - (scroll.visible ? scroll.width : 0)

        // TODO
        property real firstColumnWidth: Math.round(width / 3)

        UM.Label
        {
            text: catalog.i18nc("@label", "Profiles")
            font: UM.Theme.getFont("medium")
        }

        RecommendedQualityProfileSelector
        {
            width: parent.width
            hasQualityOptions: recommendedResolutionSelector.visible
        }

        RecommendedResolutionSelector
        {
            id: recommendedResolutionSelector
            width: parent.width
        }

        UnsupportedProfileIndication
        {
            width: parent.width
            visible: !recommendedResolutionSelector.visible
        }

        Item { height: UM.Theme.getSize("default_margin").height } // Spacer

        ProfileWarningReset
        {
            width: parent.width
        }

        Item { height: UM.Theme.getSize("thin_margin").height  + UM.Theme.getSize("narrow_margin").height} // Spacer

        //Line between the sections.
        Rectangle
        {
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
            color: UM.Theme.getColor("lining")
        }

        Item { height: UM.Theme.getSize("narrow_margin").height } //Spacer

        Column
        {
            id: settingColumn
            width: parent.width
            spacing: UM.Theme.getSize("thin_margin").height

            Item
            {
                id: recommendedPrintSettingsHeader
                height: childrenRect.height
                width: parent.width
                UM.Label
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    text: catalog.i18nc("@label", "Recommended print settings")
                    font: UM.Theme.getFont("medium")
                }

                Cura.SecondaryButton
                {
                    id: customSettingsButton
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    text: catalog.i18nc("@button", "Show Custom")
                    textFont: UM.Theme.getFont("medium_bold")
                    outlineColor: "transparent"
                    onClicked: onModeChanged()
                }
            }

            RecommendedStrengthSelector
            {
                width: parent.width
            }

            RecommendedSupportSelector
            {
                width: parent.width
            }

            RecommendedAdhesionSelector
            {
                width: parent.width
            }
        }
    }

    UM.SettingPropertyProvider
    {
        id: extrudersEnabledCount
        containerStack: Cura.MachineManager.activeMachine
        key: "extruders_enabled_count"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }
}
