// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15
import QtQuick.Layouts 2.10

import UM 1.7 as UM
import Cura 1.7 as Cura


RecommendedSettingSection
{
    id: strengthSection

    title: catalog.i18nc("@label", "Strength")
    icon: UM.Theme.getIcon("Hammer")
    enableSectionSwitchVisible: false
    enableSectionSwitchEnabled: false
    tooltipText: ""

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
            settingName: catalog.i18nc("infill_sparse_density description", "Infill Density")
            tooltipText: catalog.i18nc("@label", "Adjusts the density of infill of the print.")
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
            tooltipText: catalog.i18nc("infill_pattern description", "The pattern of the infill material of the print. The line and zig zag infill swap direction on alternate layers, reducing material cost. The grid, triangle, tri-hexagon, cubic, octet, quarter cubic, cross and concentric patterns are fully printed every layer. Gyroid, cubic, quarter cubic and octet infill change with every layer to provide a more equal distribution of strength over each direction. Lightning infill tries to minimize the infill, by only supporting the ceiling of the object.")

            settingControl: Cura.SingleSettingComboBox
            {
                width: parent.width
                settingName: "infill_pattern"
            }
        },
        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Shell Thickness")

            settingControl: RowLayout
            {
                anchors.fill: parent
                spacing: UM.Theme.getSize("default_margin").width
                UM.ComponentWithIcon
                {
                    Layout.fillWidth: true
                    source: UM.Theme.getIcon("PrintWalls")
                    displayComponent: Cura.SingleSettingTextField
                    {
                        width: parent.width
                        settingName: "wall_thickness"
                        validator: Cura.FloatValidator {}
                        unitText: catalog.i18nc("@label", "mm")
                    }
                }
                UM.ComponentWithIcon
                {
                    Layout.fillWidth: true
                    source: UM.Theme.getIcon("PrintTopBottom")
                    displayComponent: Cura.SingleSettingTextField
                    {
                        width: parent.width
                        settingName: "top_bottom_thickness"
                        validator: Cura.FloatValidator {}
                        unitText: catalog.i18nc("@label", "mm")
                    }
                }
            }
        }
    ]
}
