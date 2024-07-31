// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.7 as Cura


RecommendedSettingSection
{
    id: enableSupportRow

    title: catalog.i18nc("@label", "Support")
    icon: UM.Theme.getIcon("Support")
    enableSectionSwitchVisible: supportEnabled.properties.enabled == "True"
    enableSectionSwitchChecked: supportEnabled.properties.value == "True"
    enableSectionSwitchEnabled: recommendedPrintSetup.settingsEnabled
    tooltipText: catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, these parts would collapse during printing.")

    function onEnableSectionChanged(state)
    {
        supportEnabled.setPropertyValue("value", state)
    }

    property UM.SettingPropertyProvider supportEnabled: UM.SettingPropertyProvider
    {
        id: supportEnabled
        containerStack: Cura.MachineManager.activeMachine
        key: "support_enable"
        watchedProperties: [ "value", "enabled", "description" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: supportExtruderProvider
        key: "support_extruder_nr"
        containerStack: Cura.MachineManager.activeMachine
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    contents: [
        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Support Type")
            tooltipText: catalog.i18nc("@label", "Chooses between the techniques available to generate support. \n\n\"Normal\" support creates a support structure directly below the overhanging parts and drops those areas straight down. \n\n\"Tree\" support creates branches towards the overhanging areas that support the model on the tips of those branches, and allows the branches to crawl around the model to support it from the build plate as much as possible.")
            isCompressed: enableSupportRow.isCompressed

            settingControl: Cura.SingleSettingComboBox
            {
                id:support
                width: parent.width
                settingName: "support_structure"
                propertyRemoveUnusedValue: false
                updateAllExtruders: false
                defaultExtruderIndex: supportExtruderProvider.properties.value
            }
        },
        RecommendedSettingItem
        {
            Layout.preferredHeight: childrenRect.height
            settingName: catalog.i18nc("@action:label", "Print with")
            tooltipText: catalog.i18nc("@label", "The extruder train to use for printing the support. This is used in multi-extrusion.")
            // Hide this component when there is only one extruder
            enabled: Cura.ExtruderManager.enabledExtruderCount > 1
            visible: Cura.ExtruderManager.enabledExtruderCount > 1
            isCompressed: enableSupportRow.isCompressed || Cura.ExtruderManager.enabledExtruderCount <= 1

            settingControl: Cura.SingleSettingExtruderSelectorBar
            {
                extruderSettingName: "support_extruder_nr"
                onSelectedIndexChanged:
                {
                    support.updateAllExtruders = true
                    support.forceUpdateSettings()
                    support.updateAllExtruders = false
                }
            }
        },
        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Placement")
            tooltipText: catalog.i18nc("support_type description", "Adjusts the placement of the support structures. The placement can be set to touching build plate or everywhere. When set to everywhere the support structures will also be printed on the model.")
            isCompressed: enableSupportRow.isCompressed

            settingControl: Cura.SingleSettingComboBox
            {
                width: parent.width
                settingName: "support_type"
                updateAllExtruders: true
                defaultExtruderIndex: supportExtruderProvider.properties.value
            }
        }
    ]
}
