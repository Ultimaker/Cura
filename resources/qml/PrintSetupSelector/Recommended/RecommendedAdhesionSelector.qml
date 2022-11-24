// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7

import UM 1.5 as UM
import Cura 1.0 as Cura


RecommendedSettingSection
{
    id: enableAdhesionRow
    height: enableAdhesionContainer.height

    title: catalog.i18nc("@label", "Adhesion")
    icon: UM.Theme.getIcon("Adhesion")
    enableSectionVisible: platformAdhesionType.properties.enabled == "True"
    enableSectionChecked: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none"
    enableSectionEnabled: recommendedPrintSetup.settingsEnabled

    property var curaRecommendedMode: Cura.RecommendedMode {}

    function onEnableSectionChanged(state) {
        curaRecommendedMode.setAdhesion(state)
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
