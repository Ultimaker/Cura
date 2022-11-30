//Copyright (c) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura

Item
{
    id: recommendedPrintSetup

    height: childrenRect.height + 2 * padding

    property bool settingsEnabled: Cura.ExtruderManager.activeExtruderStackId || extrudersEnabledCount.properties.value == 1
    property real padding: UM.Theme.getSize("default_margin").width

    function onModeChanged() {}

    ColumnLayout
    {
        spacing: UM.Theme.getSize("default_margin").height

        anchors
        {
            left: parent.left
            right: parent.right
            top: parent.top
            margins: parent.padding
        }

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
            Layout.fillWidth: true
            width: parent.width
        }

        UnsupportedProfileIndication
        {
            width: parent.width
            visible: !recommendedResolutionSelector.visible
            Layout.fillWidth: true
        }


        ProfileWarningReset
        {
            width: parent.width
            Layout.fillWidth: true
            Layout.topMargin: UM.Theme.getSize("default_margin").height
            Layout.bottomMargin: UM.Theme.getSize("thin_margin").height
        }

        //Line between the sections.
        Rectangle
        {
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
            Layout.topMargin: UM.Theme.getSize("narrow_margin").height
            Layout.bottomMargin: UM.Theme.getSize("narrow_margin").height
            Layout.fillWidth: true
            color: UM.Theme.getColor("lining")
        }
        ColumnLayout
        {
            spacing: UM.Theme.getSize("thin_margin").height

            RowLayout
            {
                UM.Label
                {
                    text: catalog.i18nc("@label", "Recommended print settings")
                    font: UM.Theme.getFont("medium")
                }

                Item { Layout.fillWidth: true } // Spacer

                Cura.SecondaryButton
                {
                    id: customSettingsButton
                    anchors.top: parent.top
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
                Layout.fillWidth: true
            }

            RecommendedSupportSelector
            {
                width: parent.width
                Layout.fillWidth: true
            }

            RecommendedAdhesionSelector {
                width: parent.width
                Layout.fillWidth: true
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
