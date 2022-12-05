// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15

import UM 1.7 as UM
import Cura 1.7 as Cura
import QtQuick.Layouts 1.3

// This silder allows changing of a single setting. Only the setting name has to be passed in to "settingName".
// All of the setting updating logic is handled by this component.
// This component allows you to choose values between minValue -> maxValue and rounds them to the nearest 10.
// If the setting is limited to a single extruder or is settable with different values per extruder use "updateAllExtruders: true"
RowLayout
{
    height: childrenRect.height
    spacing: UM.Theme.getSize("default_margin").width

    property alias settingName: propertyProvider.key
    property alias enabled: settingSlider.enabled

    // If true, all extruders will have "settingName" property updated.
    // The displayed value will be read from the extruder with index "defaultExtruderIndex" instead of the machine.
    property bool updateAllExtruders: false
    // This is only used if updateAllExtruders == true
    property int defaultExtruderIndex: 0

    property bool roundToNearestTen: false
    property int maxValue: 100
    property int minValue: 0
    property int previousValue: -1

    UM.SettingPropertyProvider
    {
        id: propertyProvider
        containerStackId: updateAllExtruders ? Cura.ExtruderManager.extruderIds[defaultExtruderIndex] : Cura.MachineManager.activeMachine.id
        watchedProperties: ["value"]
        storeIndex: 0
    }

    UM.Label { Layout.fillWidth: false; text: minValue }

    UM.Slider
    {
        id: settingSlider
        Layout.fillWidth: true

        width: parent.width

        from: minValue; to: maxValue; stepSize: 1

        // set initial value from stack
        value: parseInt(propertyProvider.properties.value)

        // When the slider is released trigger an update immediately. This forces the slider to snap to the rounded value.
        onPressedChanged: if(!pressed) { roundSliderValueUpdateSetting() }
    }

    UM.Label { Layout.fillWidth: false; text: maxValue }

    Connections
    {
        target: propertyProvider
        function onContainerStackChanged() { updateTimer.restart() }
        function onIsValueUsedChanged() { updateTimer.restart() }
    }

    // Updates to the setting are delayed by interval. This reduces lag by waiting a bit after a setting change to update the slider contents.
    Timer
    {
        id: updateTimer
        interval: 100
        repeat: false
        onTriggered: parseValueUpdateSetting(false)
    }

    function updateSlider(value)
    {
        settingSlider.value = value
    }

    function roundSliderValueUpdateSetting()
    {
        // If the user interacts with the slider we round the value and update the setting.
        print("roundSliderValueUpdateSetting()")
        const roundedSliderValue = roundToNearestTen ? Math.round(settingSlider.value / 10) * 10 : Math.round(settingSlider.value)
        settingSlider.value = roundedSliderValue
        updateSetting(roundedSliderValue)
    }


    function parseValueUpdateSetting(triggerUpdate)
    {
        // Only run when the setting value is updated by something other than the slider.
        // This sets the slider value based on the setting value, it does not update the setting value.

        if (parseInt(propertyProvider.properties.value) == settingSlider.value)
        {
            return
        }

        settingSlider.value = propertyProvider.properties.value
    }

    // Override this function to update a setting differently
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
