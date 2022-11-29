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
    enableSectionVisible: false
    enableSectionEnabled: false

    contents: [
        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Infill Density")
            tooltipText: catalog.i18nc("@label", "Gradual infill will gradually increase the amount of infill towards the top.")
            settingControl: InfillSlider
            {
                height: UM.Theme.getSize("combobox").height
                width: parent.width
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
