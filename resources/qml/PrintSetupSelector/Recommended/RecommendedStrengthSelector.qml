// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.7 as Cura


RecommendedSettingSection
{
    id: strengthSection

    title: catalog.i18nc("@label", "Strength")
    icon: UM.Theme.getIcon("Hammer")
    enableSectionSwitchVisible: false
    enableSectionSwitchEnabled: false

    UM.SettingPropertyProvider
    {
        id: infillSteps
        containerStackId: Cura.MachineManager.activeStackId
        key: "gradual_infill_steps"
        watchedProperties: ["value", "enabled"]
        storeIndex: 0
    }

    contents: [
        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Infill Density")
            tooltipText: catalog.i18nc("@label", "Gradual infill will gradually increase the amount of infill towards the top.")
            settingControl: Cura.SingleSettingSlider
            {
                height: UM.Theme.getSize("combobox").height
                width: parent.width
                settingName: "infill_sparse_density"
                roundToNearestTen: true
                // disable slider when gradual support is enabled
                enabled: parseInt(infillSteps.properties.value) == 0

                function updateSetting(value)
                {
                    Cura.MachineManager.setSettingForAllExtruders("infill_sparse_density", "value", value)
                    Cura.MachineManager.resetSettingForAllExtruders("infill_line_distance")
                }
            }
        },
        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Infill Pattern")

            settingControl: Cura.SingleSettingComboBox
            {
                width: parent.width
                height: UM.Theme.getSize("combobox").height
                settingName: "infill_pattern"
            }
        }
    ]
}
