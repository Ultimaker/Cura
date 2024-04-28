// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.7 as Cura

// This ComboBox allows changing of a single setting. Only the setting name has to be passed in to "settingName".
// All of the setting updating logic is handled by this component.
// This uses the "options" value of a setting to populate the drop down. This will only work for settings with "options"
// If the setting is limited to a single extruder or is settable with different values per extruder use "updateAllExtruders: true"
Cura.ComboBox {
    textRole: "text"
    property alias settingName: propertyProvider.key
    property alias propertyRemoveUnusedValue: propertyProvider.removeUnusedValue

    // If true, all extruders will have "settingName" property updated.
    // The displayed value will be read from the extruder with index "defaultExtruderIndex" instead of the machine.
    property bool updateAllExtruders: false
    // This is only used if updateAllExtruders == true
    property int defaultExtruderIndex: Cura.ExtruderManager.activeExtruderIndex

    model:  ListModel
    {
        id: comboboxModel

        // The propertyProvider has not loaded the setting when this components onComplete triggers. Populating the model
        // is deferred until propertyProvider signals "onIsValueUsedChanged". The deferred update is triggered with this function.
        function updateModel()
        {
            clear()

            if(!propertyProvider.properties.options) // No options have been loaded yet to populate combobox
            {
                return
            }

            for (var i = 0; i < propertyProvider.properties["options"].keys().length; i++)
            {
                var key = propertyProvider.properties["options"].keys()[i]
                var value = propertyProvider.properties["options"][key]
                comboboxModel.append({ text: value, code: key})

                if (propertyProvider.properties.value === key)
                {
                    // The combobox is cleared after each value change so the currentIndex must be set each time.
                    currentIndex = i
                }
            }
        }
    }

    // Updates to the setting are delayed by interval. The signal onIsValueUsedChanged() is emitted early for some reason.
    // This causes the selected value in the combobox to be updated to the previous value. (This issue is present with infill_pattern setting)
    // This is a hack. If you see this in the future, try removing it and see if the combobox still works.
    Timer
    {
        id: updateTimer
        interval: 100
        repeat: false
        onTriggered: comboboxModel.updateModel(false)
    }

    property UM.SettingPropertyProvider propertyProvider: UM.SettingPropertyProvider
    {
        id: propertyProvider
        containerStackId: updateAllExtruders ? Cura.ExtruderManager.extruderIds[defaultExtruderIndex] : Cura.MachineManager.activeMachine.id
        removeUnusedValue: false
        watchedProperties: ["value", "validationState",  "resolve", "options"]
    }

    Connections
    {
        target: propertyProvider
        function onContainerStackChanged() { updateTimer.restart() }
        function onIsValueUsedChanged() { updateTimer.restart() }
    }

    onCurrentIndexChanged: parseValueAndUpdateSetting()

    function parseValueAndUpdateSetting()
    {
        if (comboboxModel.get(currentIndex) && comboboxModel.get(currentIndex).code !== propertyProvider.properties.value)
        {
            updateSetting(comboboxModel.get(currentIndex).code)
        }

    }
    function forceUpdateSettings()
    {
        comboboxModel.updateModel();
    }

    function updateSetting(value)
    {
        if (updateAllExtruders)
        {
            Cura.MachineManager.setSettingForAllExtruders(propertyProvider.key, "value", value)
        }
        else
        {
            propertyProvider.setPropertyValue("value", value)
        }
    }
}
