// Copyright (c) 2022 UltiMaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.7 as Cura

// This ComboBox allows changing of a single setting. Only the setting name has to be passed in to "settingName".
// All of the setting updating logic is handled by this component.
// This uses the "options" value of a setting to populate the drop down. This will only work for settings with "options"
Cura.ComboBox {
    textRole: "text"
    property alias settingName: propertyProvider.key

    model:  ListModel {
        id: comboboxModel

        // The propertyProvider has not loaded the setting when this components onComplete triggers. Populating the model
        // is defered until propertyProvider signals "onIsValueUsedChanged".
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

                if (propertyProvider.properties.value == key)
                {
                    // The combobox is cleared after each value change so the currentIndex must be set each time.
                    currentIndex = i
                }
            }
        }
    }

    property UM.SettingPropertyProvider propertyProvider: UM.SettingPropertyProvider
    {
        id: propertyProvider
        containerStack: Cura.MachineManager.activeMachine
        watchedProperties: [ "value" , "options"]
    }

    Connections
    {
        target: propertyProvider
        function onContainerStackChanged() { comboboxModel.updateModel() }
        function onIsValueUsedChanged() { comboboxModel.updateModel() }
    }

    onCurrentIndexChanged: propertyProvider.setPropertyValue("value", comboboxModel.get(currentIndex).code)
}
