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

        UM.Label
        {
            text: catalog.i18nc("@label", "Print settings")
            font: UM.Theme.getFont("medium")
        }

        RecommendedStrengthSelector
        {
            width: parent.width
            labelColumnWidth: parent.firstColumnWidth
            Layout.fillWidth: true
            Layout.rightMargin: UM.Theme.getSize("default_margin").width
        }

        RecommendedSupportSelector
        {
            width: parent.width
            labelColumnWidth: parent.firstColumnWidth
            Layout.fillWidth: true
        }

        RecommendedAdhesionSelector
        {
            width: parent.width
            labelColumnWidth: parent.firstColumnWidth
            Layout.fillWidth: true
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
