// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.7 as UM
import Cura 1.7 as Cura

// This text field allows you to edit a single setting. The setting can be passed by "settingName".
// You must specify a validator with Validator. We store our default setting validators in qml/Validators
// If the setting is limited to a single extruder or is settable with different values per extruder use "updateAllExtruders: true"
UM.TextField
{
    id: control
    property alias settingName: propertyProvider.key

    // If true, all extruders will have "settingName" property updated.
    // The displayed value will be read from the extruder with index "defaultExtruderIndex" instead of the machine.
    property bool updateAllExtruders: false
    // This is only used if updateAllExtruders == true
    property int defaultExtruderIndex: Cura.ExtruderManager.activeExtruderIndex

    // Resolving the value in the textField.
    Binding
    {
        target: control
        property: "text"

        value:
        {
            if (control.activeFocus)
            {
                // This stops the text being reformatted as you edit. For example "10.1" -Edit-> "10." -Auto Format-> "10.0".
                return control.text
            }

            if (( propertyProvider.properties.resolve != "None" &&  propertyProvider.properties.resolve) && ( propertyProvider.properties.stackLevels[0] != 0) && ( propertyProvider.properties.stackLevels[0] != 1))
            {
                // We have a resolve function. Indicates that the setting is not settable per extruder and that
                // we have to choose between the resolved value (default) and the global value
                // (if user has explicitly set this).
                return base.resolve
            }

            return propertyProvider.properties.value
        }

    }

    property UM.SettingPropertyProvider propertyProvider: UM.SettingPropertyProvider
    {
        id: propertyProvider
        watchedProperties: ["value", "validationState",  "resolve"]
        removeUnusedValue: false
        containerStackId: updateAllExtruders ? Cura.ExtruderManager.extruderIds[defaultExtruderIndex] : Cura.MachineManager.activeMachine.id
    }

    Connections
    {
        target: propertyProvider
        function onContainerStackChanged()
        {
            updateTimer.restart()
        }
        function onIsValueUsedChanged()
        {
            updateTimer.restart()
        }
    }

    // Restart update timer right after releasing a key. This stops lag while typing, but you still get warning and error
    // textfield styling while typing.
    Keys.onReleased: updateTimer.restart()
    // Forces formatting when you finish editing "10.1" -Edit-> "10." -Focus Change-> "10"
    onActiveFocusChanged: updateTimer.restart()

    // Updates to the setting are delayed by interval. This stops lag caused by calling the
    // parseValueUpdateSetting() function being called repeatedly while changing the text value.
    Timer
    {
        id: updateTimer
        interval: 50
        repeat: false
        onTriggered: parseValueUpdateSetting()
    }

    function parseValueUpdateSetting()
    {
        // User convenience. We use dots for decimal values
        const modified_text = text.replace(",", ".");
        if (propertyProvider.properties.value === modified_text || (parseFloat(propertyProvider.properties.value) === parseFloat(modified_text)))
        {
            // Don't set the property value from the control. It already has the same value
            return
        }

        if (propertyProvider && modified_text !== propertyProvider.properties.value)
        {
            updateSetting(modified_text);
        }
    }

    function updateSetting(value)
    {
        if (updateAllExtruders)
        {
            Cura.MachineManager.setSettingForAllExtruders(propertyProvider.key, "value", value)
        }
        else
        {
            propertyProvider.setPropertyValue("value", text)
        }
    }

    // Forced to override parent states using overrideState. Otherwise hover in TextField.qml would override the validation states.
    // The first state to evaluate true applies styling. States in inheriting components get appended to the state list of their parent.
    overrideState: true
    states:
    [
        State
        {
            name: "validationError"
            when: propertyProvider.properties.validationState === "ValidatorState.Exception" || propertyProvider.properties.validationState === "ValidatorState.MinimumError" || propertyProvider.properties.validationState === "ValidatorState.MaximumError"
             PropertyChanges
             {
                target: background
                liningColor: UM.Theme.getColor("setting_validation_error")
                color: UM.Theme.getColor("setting_validation_error_background")
             }
        },
        State
        {
            name: "validationWarning"
            when: propertyProvider.properties.validationState === "ValidatorState.MinimumWarning" || propertyProvider.properties.validationState === "ValidatorState.MaximumWarning"
            PropertyChanges
            {
                target: background
                liningColor: UM.Theme.getColor("setting_validation_warning")
                color: UM.Theme.getColor("setting_validation_warning_background")
            }
        },
        State
        {
            name: "disabled"
            when: !control.enabled
            PropertyChanges
            {
                target: control
                color: UM.Theme.getColor("text_field_text_disabled")
            }
            PropertyChanges
            {
                target: background
                liningColor: UM.Theme.getColor("text_field_border_disabled")
            }
        },
        State
        {
            name: "invalid"
            when: !control.acceptableInput
            PropertyChanges
            {
                target: background
                color: UM.Theme.getColor("setting_validation_error_background")
            }
        },
        State
        {
            name: "active"
            when: control.activeFocus
            PropertyChanges
            {
                target: background
                liningColor: UM.Theme.getColor("text_field_border_active")
                borderColor: UM.Theme.getColor("text_field_border_active")
            }
        },
        State
        {
            name: "hovered"
            when: control.hovered && !control.activeFocus
            PropertyChanges
            {
                target: background
                liningColor: UM.Theme.getColor("text_field_border_hovered")
            }
        }
    ]
}
