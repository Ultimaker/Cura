// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM
import Cura 1.0 as Cura

Item
{
    id: sliderRoot

    // Handle properties
    property real handleSize: UM.Theme.getSize("slider_handle").width
    property real handleRadius: handleSize / 2
    property real minimumRangeHandleSize: handleSize / 2
    property color upperHandleColor: UM.Theme.getColor("slider_handle")
    property color lowerHandleColor: UM.Theme.getColor("slider_handle")
    property color rangeHandleColor: UM.Theme.getColor("slider_groove_fill")
    property color handleActiveColor: UM.Theme.getColor("slider_handle_active")
    property var activeHandle: upperHandle

    // Track properties
    property real trackThickness: UM.Theme.getSize("slider_groove").width // width of the slider track
    property real trackRadius: UM.Theme.getSize("slider_groove_radius").width
    property color trackColor: UM.Theme.getColor("slider_groove")

    // value properties
    property real maximumValue: 100
    property real minimumValue: 0
    property real minimumRange: 0 // minimum range allowed between min and max values
    property bool roundValues: true
    property real upperValue: maximumValue
    property real lowerValue: minimumValue

    property bool layersVisible: true
    property bool manuallyChanged: true     // Indicates whether the value was changed manually or during simulation

    function getUpperValueFromSliderHandle()
    {
        return upperHandle.getValue()
    }

    function setUpperValue(value)
    {
        upperHandle.setValue(value)
        updateRangeHandle()
    }

    function getLowerValueFromSliderHandle()
    {
        return lowerHandle.getValue()
    }

    function setLowerValue(value)
    {
        lowerHandle.setValue(value)
        updateRangeHandle()
    }

    function updateRangeHandle()
    {
        rangeHandle.height = lowerHandle.y - (upperHandle.y + upperHandle.height)
    }

    // set the active handle to show only one label at a time
    function setActiveHandle(handle)
    {
        activeHandle = handle
    }

    function normalizeValue(value)
    {
        return Math.min(Math.max(value, sliderRoot.minimumValue), sliderRoot.maximumValue)
    }

    // Slider track
    Rectangle
    {
        id: track

        width: sliderRoot.trackThickness
        height: sliderRoot.height - sliderRoot.handleSize
        radius: sliderRoot.trackRadius
        anchors.centerIn: sliderRoot
        color: sliderRoot.trackColor
        visible: sliderRoot.layersVisible
    }

    // Range handle
    Item
    {
        id: rangeHandle

        y: upperHandle.y + upperHandle.height
        width: sliderRoot.handleSize
        height: sliderRoot.minimumRangeHandleSize
        anchors.horizontalCenter: sliderRoot.horizontalCenter
        visible: sliderRoot.layersVisible

        // Set the new value when dragging
        function onHandleDragged()
        {
            sliderRoot.manuallyChanged = true

            upperHandle.y = y - upperHandle.height
            lowerHandle.y = y + height

            var upperValue = sliderRoot.getUpperValueFromSliderHandle()
            var lowerValue = sliderRoot.getLowerValueFromSliderHandle()

            // set both values after moving the handle position
            UM.SimulationView.setCurrentLayer(upperValue)
            UM.SimulationView.setMinimumLayer(lowerValue)
        }

        function setValueManually(value)
        {
            sliderRoot.manuallyChanged = true
            upperHandle.setValue(value)
        }

        function setValue(value)
        {
            var range = sliderRoot.upperValue - sliderRoot.lowerValue
            value = Math.min(value, sliderRoot.maximumValue)
            value = Math.max(value, sliderRoot.minimumValue + range)

            UM.SimulationView.setCurrentLayer(value)
            UM.SimulationView.setMinimumLayer(value - range)
        }

        Rectangle
        {
            width: sliderRoot.trackThickness
            height: parent.height + sliderRoot.handleSize
            anchors.centerIn: parent
            radius: sliderRoot.trackRadius
            color: sliderRoot.rangeHandleColor
        }

        MouseArea
        {
            anchors.fill: parent

            drag
            {
                target: parent
                axis: Drag.YAxis
                minimumY: upperHandle.height
                maximumY: sliderRoot.height - (rangeHandle.height + lowerHandle.height)
            }

            onPositionChanged: parent.onHandleDragged()
            onPressed: sliderRoot.setActiveHandle(rangeHandle)
        }

    }

    onHeightChanged : {
        // After a height change, the pixel-position of the lower handle is out of sync with the property value
        setLowerValue(lowerValue)
    }

    // Upper handle
    Rectangle
    {
        id: upperHandle

        y: sliderRoot.height - (sliderRoot.minimumRangeHandleSize + 2 * sliderRoot.handleSize)
        width: sliderRoot.handleSize
        height: sliderRoot.handleSize
        anchors.horizontalCenter: sliderRoot.horizontalCenter
        radius: sliderRoot.handleRadius
        color: upperHandleLabel.activeFocus ? sliderRoot.handleActiveColor : sliderRoot.upperHandleColor
        visible: sliderRoot.layersVisible

        function onHandleDragged()
        {
            sliderRoot.manuallyChanged = true

            // don't allow the lower handle to be heigher than the upper handle
            if (lowerHandle.y - (y + height) < sliderRoot.minimumRangeHandleSize)
            {
                lowerHandle.y = y + height + sliderRoot.minimumRangeHandleSize
            }

            // update the range handle
            sliderRoot.updateRangeHandle()

            // set the new value after moving the handle position
            UM.SimulationView.setCurrentLayer(getValue())
        }

        // get the upper value based on the slider position
        function getValue()
        {
            var result = y / (sliderRoot.height - (2 * sliderRoot.handleSize + sliderRoot.minimumRangeHandleSize))
            result = sliderRoot.maximumValue + result * (sliderRoot.minimumValue - (sliderRoot.maximumValue - sliderRoot.minimumValue))
            result = sliderRoot.roundValues ? Math.round(result) : result
            return result
        }

        function setValueManually(value)
        {
            sliderRoot.manuallyChanged = true
            upperHandle.setValue(value)
        }

        // set the slider position based on the upper value
        function setValue(value)
        {
            // Normalize values between range, since using arrow keys will create out-of-the-range values
            value = sliderRoot.normalizeValue(value)

            UM.SimulationView.setCurrentLayer(value)

            var diff = (value - sliderRoot.maximumValue) / (sliderRoot.minimumValue - sliderRoot.maximumValue)
            // In case there is only one layer, the diff value results in a NaN, so this is for catching this specific case
            if (isNaN(diff))
            {
                diff = 0
            }
            var newUpperYPosition = Math.round(diff * (sliderRoot.height - (2 * sliderRoot.handleSize + sliderRoot.minimumRangeHandleSize)))
            y = newUpperYPosition

            // update the range handle
            sliderRoot.updateRangeHandle()
        }

        Keys.onUpPressed: upperHandleLabel.setValue(upperHandleLabel.value + ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))
        Keys.onDownPressed: upperHandleLabel.setValue(upperHandleLabel.value - ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))

        // dragging
        MouseArea
        {
            anchors.fill: parent

            drag
            {
                target: parent
                axis: Drag.YAxis
                minimumY: 0
                maximumY: sliderRoot.height - (2 * sliderRoot.handleSize + sliderRoot.minimumRangeHandleSize)
            }

            onPositionChanged: parent.onHandleDragged()
            onPressed:
            {
                sliderRoot.setActiveHandle(upperHandle)
                upperHandleLabel.forceActiveFocus()
            }
        }

        SimulationSliderLabel
        {
            id: upperHandleLabel

            height: sliderRoot.handleSize + UM.Theme.getSize("small_margin").height
            anchors.bottom: parent.top
            anchors.bottomMargin: UM.Theme.getSize("narrow_margin").height
            anchors.horizontalCenter: parent.horizontalCenter
            target: Qt.point(parent.width / 2, parent.top)
            visible: sliderRoot.activeHandle == parent || sliderRoot.activeHandle == rangeHandle

            // custom properties
            maximumValue: sliderRoot.maximumValue
            value: sliderRoot.upperValue
            busy: UM.SimulationView.busy
            setValue: upperHandle.setValueManually // connect callback functions
        }
    }

    // Lower handle
    Rectangle
    {
        id: lowerHandle

        y: sliderRoot.height - sliderRoot.handleSize
        width: parent.handleSize
        height: parent.handleSize
        anchors.horizontalCenter: parent.horizontalCenter
        radius: sliderRoot.handleRadius
        color: lowerHandleLabel.activeFocus ? sliderRoot.handleActiveColor : sliderRoot.lowerHandleColor

        visible: sliderRoot.layersVisible

        function onHandleDragged()
        {
            sliderRoot.manuallyChanged = true

            // don't allow the upper handle to be lower than the lower handle
            if (y - (upperHandle.y + upperHandle.height) < sliderRoot.minimumRangeHandleSize)
            {
                upperHandle.y = y - (upperHandle.heigth + sliderRoot.minimumRangeHandleSize)
            }

            // update the range handle
            sliderRoot.updateRangeHandle()

            // set the new value after moving the handle position
            UM.SimulationView.setMinimumLayer(getValue())
        }

        // get the lower value from the current slider position
        function getValue()
        {
            var result = (y - (sliderRoot.handleSize + sliderRoot.minimumRangeHandleSize)) / (sliderRoot.height - (2 * sliderRoot.handleSize + sliderRoot.minimumRangeHandleSize));
            result = sliderRoot.maximumValue - sliderRoot.minimumRange + result * (sliderRoot.minimumValue - (sliderRoot.maximumValue - sliderRoot.minimumRange))
            result = sliderRoot.roundValues ? Math.round(result) : result
            return result
        }

        function setValueManually(value)
        {
            sliderRoot.manuallyChanged = true
            lowerHandle.setValue(value)
        }

        // set the slider position based on the lower value
        function setValue(value)
        {
            // Normalize values between range, since using arrow keys will create out-of-the-range values
            value = sliderRoot.normalizeValue(value)

            UM.SimulationView.setMinimumLayer(value)

            var diff = (value - sliderRoot.maximumValue) / (sliderRoot.minimumValue - sliderRoot.maximumValue)
            // In case there is only one layer, the diff value results in a NaN, so this is for catching this specific case
            if (isNaN(diff))
            {
                diff = 0
            }
            var newLowerYPosition = Math.round((sliderRoot.handleSize + sliderRoot.minimumRangeHandleSize) + diff * (sliderRoot.height - (2 * sliderRoot.handleSize + sliderRoot.minimumRangeHandleSize)))
            y = newLowerYPosition

            // update the range handle
            sliderRoot.updateRangeHandle()
        }

        Keys.onUpPressed: lowerHandleLabel.setValue(lowerHandleLabel.value + ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))
        Keys.onDownPressed: lowerHandleLabel.setValue(lowerHandleLabel.value - ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))

        // dragging
        MouseArea
        {
            anchors.fill: parent

            drag
            {
                target: parent
                axis: Drag.YAxis
                minimumY: upperHandle.height + sliderRoot.minimumRangeHandleSize
                maximumY: sliderRoot.height - parent.height
            }

            onPositionChanged: parent.onHandleDragged()
            onPressed:
            {
                sliderRoot.setActiveHandle(lowerHandle)
                lowerHandleLabel.forceActiveFocus()
            }
        }

        SimulationSliderLabel
        {
            id: lowerHandleLabel

            height: sliderRoot.handleSize + UM.Theme.getSize("small_margin").height
            anchors.top: parent.bottom
            anchors.topMargin: UM.Theme.getSize("narrow_margin").height
            anchors.horizontalCenter: parent.horizontalCenter
            target: Qt.point(parent.width / 2, parent.bottom)
            visible: sliderRoot.activeHandle == parent || sliderRoot.activeHandle == rangeHandle

            // custom properties
            maximumValue: sliderRoot.maximumValue
            value: sliderRoot.lowerValue
            busy: UM.SimulationView.busy
            setValue: lowerHandle.setValueManually // connect callback functions
        }
    }
}
