// Copyright (c) 2022 Ultimaker B.V.
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
    enableSectionVisible: supportEnabled.properties.enabled == "True"
    enableSectionChecked: supportEnabled.properties.value == "True"
    enableSectionEnabled: recommendedPrintSetup.settingsEnabled
    toolTipText: catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, such parts would collapse during printing.")

    function onEnableSectionChanged(state) {
        supportEnabled.setPropertyValue("value", state)
    }

    property var extruderModel: CuraApplication.getExtrudersModel()


    property UM.SettingPropertyProvider supportEnabled: UM.SettingPropertyProvider
    {
        id: supportEnabled
        containerStack: Cura.MachineManager.activeMachine
        key: "support_enable"
        watchedProperties: [ "value", "enabled", "description" ]
        storeIndex: 0
    }

    property UM.SettingPropertyProvider supportExtruderNr: UM.SettingPropertyProvider
    {
        containerStack: Cura.MachineManager.activeMachine
        key: "support_extruder_nr"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    property UM.SettingPropertyProvider machineExtruderCount: UM.SettingPropertyProvider
    {
        containerStack: Cura.MachineManager.activeMachine
        key: "machine_extruder_count"
        watchedProperties: ["value"]
        storeIndex: 0
    }

    contents: [
        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Support Type")

            settingControl: Cura.SingleSettingComboBox
            {
                width: parent.width
                height: UM.Theme.getSize("combobox").height
                settingName: "support_structure"
            }
        },
        RecommendedSettingItem
        {
            Layout.preferredHeight: childrenRect.height
            settingName: catalog.i18nc("@action:label", "Print with")
            settingControl: Cura.ExtruderSelectorBar
            {
                model: extruderModel
                selectedIndex: supportExtruderNr.properties.value !== undefined ? supportExtruderNr.properties.value : 0
                function onClickExtruder(index)
                {
                    forceActiveFocus();
                    supportExtruderNr.setPropertyValue("value", index);
                }
            }

        },

        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Placement")

            settingControl: Cura.SingleSettingComboBox
            {
                width: parent.width
                height: UM.Theme.getSize("combobox").height
                settingName: "support_type"
            }
        }
    ]
}
