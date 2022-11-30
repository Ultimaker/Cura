// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15

import UM 1.7 as UM
import Cura 1.7 as Cura
import QtQuick.Layouts 1.3

RowLayout
{
    height: childrenRect.height
    spacing: UM.Theme.getSize("default_margin").width

    property alias settingName: settingPropertyProvider.key
    property alias enabled: settingSlider.enabled

    property bool roundToNearestTen: false
    property int maxValue: 100
    property int minValue: 0

    anchors
    {
        left: strengthSection.right
        right: parent.right
        verticalCenter: strengthSection.verticalCenter
    }

    UM.SettingPropertyProvider
    {
        id: settingPropertyProvider
        containerStackId: Cura.MachineManager.activeStackId
        watchedProperties: [ "value" ]
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
        value: parseInt(settingPropertyProvider.properties.value)

        // When the slider is released trigger an update immediately. This forces the slider to snap to the rounded value.
        onPressedChanged: if(!pressed) { parseValueUpdateSetting() }
    }

    UM.Label { Layout.fillWidth: false; text: maxValue }

    Connections
    {
        target: settingPropertyProvider
        function onContainerStackChanged() { updateTimer.restart() }
        function onIsValueUsedChanged() { updateTimer.restart() }
    }

    // Updates to the setting are delayed by interval. This stops lag caused by calling the
    // parseValueUpdateSetting() function being call repeatedly while dragging the slider.
    Timer
    {
        id: updateTimer
        interval: 100
        repeat: false
        onTriggered:
        {
            parseValueUpdateSetting()
        }
    }

    function parseValueUpdateSetting()
    {
        // Work around, the `settingPropertyProvider.properties.value` is initially `undefined`. As
        // `parseInt(settingPropertyProvider.properties.value)` is parsed as 0 and is initially set as
        // the slider value. By setting this 0 value an update is triggered setting the actual
        // sitting value to 0.
        if (isNaN(parseInt(settingPropertyProvider.properties.value)))
        {
            return;
        }

        // Don't update if the setting value, if the slider has the same value
        if (parseInt(settingPropertyProvider.properties.value) == settingSlider.value)
        {
            return;
        }

        // Round the slider value to the nearest multiple of 10 (simulate step size of 10)
        const roundedSliderValue = roundToNearestTen ? Math.round(settingSlider.value / 10) * 10 : Math.round(settingSlider.value)

        // Update the slider value to represent the rounded value
        settingSlider.value = roundedSliderValue;

        updateSetting(roundedSliderValue);
    }

    // Override this function to update a setting differently
    function updateSetting(value) {
        propertyProvider.setPropertyValue("value", value)
    }
}
