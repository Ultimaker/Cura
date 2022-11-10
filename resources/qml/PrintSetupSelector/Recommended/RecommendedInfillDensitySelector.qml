// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura


//
// Infill
//
Item
{
    id: infillRow
    height: UM.Theme.getSize("print_setup_big_item").height

    property real labelColumnWidth: Math.round(width / 3)

    // Create a binding to update the icon when the infill density changes
    Binding
    {
        target: infillRowTitle
        property: "source"
        value:
        {
            var density = parseInt(infillDensity.properties.value)
            if (density <= 0)
            {
                return UM.Theme.getIcon("Infill0")
            }
            if (density < 40)
            {
                return UM.Theme.getIcon("Infill3")
            }
            if (density < 90)
            {
                return UM.Theme.getIcon("Infill2")
            }
            return UM.Theme.getIcon("Infill100")
        }
    }

    // We use a binding to make sure that after manually setting infillSlider.value it is still bound to the property provider
    Binding
    {
        target: infillSlider
        property: "value"
        value: {
            // The infill slider has a max value of 100. When it is given a value > 100 onValueChanged updates the setting to be 100.
            // When changing to an intent with infillDensity > 100, it would always be clamped to 100.
            // This will force the slider to ignore the first onValueChanged for values > 100 so higher values can be set.
            var density = parseInt(infillDensity.properties.value)
            if (density > 100) {
                infillSlider.ignoreValueChange = true
            }

            return density
        }
    }

    // Here are the elements that are shown in the left column
    Cura.IconWithText
    {
        id: infillRowTitle
        anchors.top: parent.top
        anchors.left: parent.left
        source: UM.Theme.getIcon("Infill1")
        text: catalog.i18nc("@label", "Infill") + " (%)"
        font: UM.Theme.getFont("medium")
        width: labelColumnWidth
        iconSize: UM.Theme.getSize("medium_button_icon").width
        tooltipText: catalog.i18nc("@label", "Adjust the density of infill of the print.")
    }

    Item
    {
        id: infillSliderContainer
        height: childrenRect.height

        anchors
        {
            left: infillRowTitle.right
            right: parent.right
            verticalCenter: infillRowTitle.verticalCenter
        }

        Slider
        {
            id: infillSlider

            property var ignoreValueChange: false

            width: parent.width
            height: UM.Theme.getSize("print_setup_slider_handle").height // The handle is the widest element of the slider

            from: 0
            to: 100
            stepSize: 1
            enabled: true

            // set initial value from stack
            value: parseInt(infillDensity.properties.value)

            //Draw line
            background: Rectangle
            {
                id: backgroundLine
                height: UM.Theme.getSize("print_setup_slider_groove").height
                width: parent.width - UM.Theme.getSize("print_setup_slider_handle").width
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                color: infillSlider.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")

                Repeater
                {
                    id: repeater
                    anchors.fill: parent
                    model: infillSlider.to / infillSlider.stepSize + 1

                    Rectangle
                    {
                        color: infillSlider.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                        implicitWidth: UM.Theme.getSize("print_setup_slider_tickmarks").width
                        implicitHeight: UM.Theme.getSize("print_setup_slider_tickmarks").height
                        anchors.verticalCenter: parent.verticalCenter

                        // Do not use Math.round otherwise the tickmarks won't be aligned
                        // (space between steps) * index of step
                        x: (backgroundLine.width / (repeater.count - 1)) * index

                        radius: Math.round(implicitWidth / 2)
                        visible: (index % 10) == 0 // Only show steps of 10%

                        UM.Label
                        {
                            text: index
                            visible: (index % 20) == 0 // Only show steps of 20%
                            anchors.horizontalCenter: parent.horizontalCenter
                            y: UM.Theme.getSize("thin_margin").height
                            color: UM.Theme.getColor("quality_slider_available")
                        }
                    }
                }
            }

            handle: Rectangle
            {
                id: handleButton
                x: infillSlider.leftPadding + infillSlider.visualPosition * (infillSlider.availableWidth - width)
                y: infillSlider.topPadding + infillSlider.availableHeight / 2 - height / 2
                color: infillSlider.enabled ? UM.Theme.getColor("primary") : UM.Theme.getColor("quality_slider_unavailable")
                implicitWidth: UM.Theme.getSize("print_setup_slider_handle").width
                implicitHeight: implicitWidth
                radius: Math.round(implicitWidth / 2)
                border.color: UM.Theme.getColor("slider_groove_fill")
                border.width: UM.Theme.getSize("default_lining").height
            }

            Connections
            {
                target: infillSlider
                function onValueChanged()
                {
                    if (infillSlider.ignoreValueChange)
                    {
                        infillSlider.ignoreValueChange = false
                        return
                    }

                    // Don't update if the setting value, if the slider has the same value
                    if (parseInt(infillDensity.properties.value) == infillSlider.value)
                    {
                        return
                    }

                    // Round the slider value to the nearest multiple of 10 (simulate step size of 10)
                    var roundedSliderValue = Math.round(infillSlider.value / 10) * 10

                    // Update the slider value to represent the rounded value
                    infillSlider.value = roundedSliderValue

                    // Update value only if the Recommended mode is Active,
                    // Otherwise if I change the value in the Custom mode the Recommended view will try to repeat
                    // same operation
                    const active_mode = UM.Preferences.getValue("cura/active_mode")

                    if (visible  // Workaround: 'visible' is checked because on startup in Windows it spuriously gets an 'onValueChanged' with value '0' if this isn't checked.
                        && (active_mode == 0 || active_mode == "simple"))
                    {
                        Cura.MachineManager.setSettingForAllExtruders("infill_sparse_density", "value", roundedSliderValue)
                        Cura.MachineManager.resetSettingForAllExtruders("infill_line_distance")
                    }
                }
            }
        }
    }

    UM.SettingPropertyProvider
    {
        id: infillDensity
        containerStackId: Cura.MachineManager.activeStackId
        key: "infill_sparse_density"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }
}
