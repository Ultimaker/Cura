// Copyright (c) 2026 UltiMaker
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
    tooltipText: catalog.i18nc("@label", "The following settings define the strength of your part.")

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
                updateAllExtruders: true
                // disable slider when gradual support is enabled
                enabled: parseInt(infillSteps.properties.value) === 0

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
            tooltipText: catalog.i18nc("@label",
            "<html>The pattern of the infill material of the print:<ul><li>For quick prints of non-functional models, choose Line, Zig Zag or Lightning infill.</li><li>For functional parts not subjected to a lot of stress we recommend Grid, Triangle, or Tri-Hexagon.</li><li>For functional 3D prints requiring high strength in multiple directions use Honeycomb, Cubic, Cubic Subdivision, Quarter Cubic, Octet, Gyroid, and Octagon.</li></ul>⚠ Grid, Triangle, and Cubic infill patterns contain intersecting lines, that may cause your nozzle to bump into printed lines, and your printer to vibrate. Use with caution.<html>")

            settingControl: Cura.SingleSettingComboBox
            {
                width: parent.width
                settingName: "infill_pattern"
                updateAllExtruders: true
                hideOptions: ["ultimaker_factor4"].includes(Cura.MachineManager.activeMachine.definition.id) ? ["grid", "triangles", "cubic"] : []
            }
        },
        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Shell Thickness")
            tooltipText: catalog.i18nc("@label", "Defines the thickness of your part side walls, roof and floor.")

            settingControl: RowLayout
            {
                anchors.fill: parent
                spacing: UM.Theme.getSize("default_margin").width
                UM.ComponentWithIcon
                {
                    Layout.fillWidth: true
                    source: UM.Theme.getIcon("PrintWalls")

                    Cura.SingleSettingTextField
                    {
                        width: parent.width
                        settingName: "wall_thickness"
                        updateAllExtruders: true
                        validator: UM.FloatValidator {}
                        unitText: catalog.i18nc("@label", "mm")
                    }
                }
                UM.ComponentWithIcon
                {
                    Layout.fillWidth: true
                    source: UM.Theme.getIcon("PrintTopBottom")

                    Cura.SingleSettingTextField
                    {
                        width: parent.width
                        settingName: "top_bottom_thickness"
                        updateAllExtruders: true
                        validator: UM.FloatValidator {}
                        unitText: catalog.i18nc("@label", "mm")
                    }
                }
            }
        }
    ]
}
