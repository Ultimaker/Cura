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

    // handle properties
    property real handleSize: UM.Theme.getSize("slider_handle").width
    property real handleRadius: handleSize / 2
    property color handleColor: UM.Theme.getColor("slider_handle")
    property color handleActiveColor: UM.Theme.getColor("slider_handle_active")
    property color rangeColor: UM.Theme.getColor("slider_groove_fill")
    property real handleLabelWidth: width

    // track properties
    property real trackThickness: UM.Theme.getSize("slider_groove").width
    property real trackRadius: UM.Theme.getSize("slider_groove_radius").width
    property color trackColor: UM.Theme.getColor("slider_groove")

    // value properties
    property real maximumValue: 100
    property real minimumValue: 0
    property bool roundValues: true
    property real handleValue: maximumValue

    property bool pathsVisible: true
    property bool manuallyChanged: true     // Indicates whether the value was changed manually or during simulation

    function getHandleValueFromSliderHandle()
    {
        return handle.getValue()
    }

    function setHandleValue(value)
    {
        handle.setValue(value)
        updateRangeHandle()
    }

    function updateRangeHandle()
    {
        rangeHandle.width = handle.x - sliderRoot.handleSize
    }

    function normalizeValue(value)
    {
        return Math.min(Math.max(value, sliderRoot.minimumValue), sliderRoot.maximumValue)
    }

    // slider track
    Rectangle
    {
        id: track

        width: sliderRoot.width - sliderRoot.handleSize
        height: sliderRoot.trackThickness
        radius: sliderRoot.trackRadius
        anchors.centerIn: sliderRoot
        color: sliderRoot.trackColor
        visible: sliderRoot.pathsVisible
    }

    // Progress indicator
    Item
    {
        id: rangeHandle

        x: handle.width
        height: sliderRoot.handleSize
        width: handle.x - sliderRoot.handleSize
        anchors.verticalCenter: sliderRoot.verticalCenter
        visible: sliderRoot.pathsVisible

        Rectangle
        {
            height: sliderRoot.trackThickness
            width: parent.width + sliderRoot.handleSize
            anchors.centerIn: parent
            radius: sliderRoot.trackRadius
            color: sliderRoot.rangeColor
        }
    }

    // Handle
    Rectangle
    {
        id: handle

        x: sliderRoot.handleSize
        width: sliderRoot.handleSize
        height: sliderRoot.handleSize
        anchors.verticalCenter: sliderRoot.verticalCenter
        radius: sliderRoot.handleRadius
        color: handleLabel.activeFocus ? sliderRoot.handleActiveColor : sliderRoot.handleColor
        visible: sliderRoot.pathsVisible

        function onHandleDragged()
        {
            sliderRoot.manuallyChanged = true

            // update the range handle
            sliderRoot.updateRangeHandle()

            // set the new value after moving the handle position
            UM.SimulationView.setCurrentPath(getValue())
        }

        // get the value based on the slider position
        function getValue()
        {
            var result = x / (sliderRoot.width - sliderRoot.handleSize)
            result = result * sliderRoot.maximumValue
            result = sliderRoot.roundValues ? Math.round(result) : result
            return result
        }

        function setValueManually(value)
        {
            sliderRoot.manuallyChanged = true
            handle.setValue(value)
        }

        // set the slider position based on the value
        function setValue(value)
        {
            // Normalize values between range, since using arrow keys will create out-of-the-range values
            value = sliderRoot.normalizeValue(value)

            UM.SimulationView.setCurrentPath(value)

            var diff = value / sliderRoot.maximumValue
            var newXPosition = Math.round(diff * (sliderRoot.width - sliderRoot.handleSize))
            x = newXPosition

            // update the range handle
            sliderRoot.updateRangeHandle()
        }

        Keys.onRightPressed: handleLabel.setValue(handleLabel.value + ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))
        Keys.onLeftPressed: handleLabel.setValue(handleLabel.value - ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))

        // dragging
        MouseArea
        {
            anchors.fill: parent

            drag
            {
                target: parent
                axis: Drag.XAxis
                minimumX: 0
                maximumX: sliderRoot.width - sliderRoot.handleSize
            }
            onPressed: handleLabel.forceActiveFocus()
            onPositionChanged: parent.onHandleDragged()
        }

        SimulationSliderLabel
        {
            id: handleLabel

            height: sliderRoot.handleSize + UM.Theme.getSize("default_margin").height
            y: parent.y + sliderRoot.handleSize + UM.Theme.getSize("default_margin").height
            anchors.horizontalCenter: parent.horizontalCenter
            target: Qt.point(x + width / 2, sliderRoot.height)
            visible: false
            startFrom: 0

            // custom properties
            maximumValue: sliderRoot.maximumValue
            value: sliderRoot.handleValue
            busy: UM.SimulationView.busy
            setValue: handle.setValueManually // connect callback functions
        }
    }
}
