// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura


//
// Quality profile
//
Item
{
    id: qualityRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)
    property real settingsColumnWidth: width - labelColumnWidth

    Timer
    {
        id: qualitySliderChangeTimer
        interval: 50
        running: false
        repeat: false
        onTriggered:
        {
            var item = Cura.QualityProfilesDropDownMenuModel.getItem(qualitySlider.value);
            Cura.MachineManager.activeQualityGroup = item.quality_group;
        }
    }

    Component.onCompleted: qualityModel.update()

    Connections
    {
        target: Cura.QualityProfilesDropDownMenuModel
        onItemsChanged: qualityModel.update()
    }

    Connections {
        target: base
        onVisibleChanged:
        {
            // update needs to be called when the widgets are visible, otherwise the step width calculation
            // will fail because the width of an invisible item is 0.
            if (visible)
            {
                qualityModel.update();
            }
        }
    }

    ListModel
    {
        id: qualityModel

        property var totalTicks: 0
        property var availableTotalTicks: 0
        property var existingQualityProfile: 0

        property var qualitySliderActiveIndex: 0
        property var qualitySliderStepWidth: 0
        property var qualitySliderAvailableMin: 0
        property var qualitySliderAvailableMax: 0
        property var qualitySliderMarginRight: 0

        function update ()
        {
            reset()

            var availableMin = -1
            var availableMax = -1

            for (var i = 0; i < Cura.QualityProfilesDropDownMenuModel.rowCount(); i++)
            {
                var qualityItem = Cura.QualityProfilesDropDownMenuModel.getItem(i)

                // Add each quality item to the UI quality model
                qualityModel.append(qualityItem)

                // Set selected value
                if (Cura.MachineManager.activeQualityType == qualityItem.quality_type)
                {
                    // set to -1 when switching to user created profile so all ticks are clickable
                    if (Cura.MachineManager.hasCustomQuality)
                    {
                        qualityModel.qualitySliderActiveIndex = -1
                    }
                    else
                    {
                        qualityModel.qualitySliderActiveIndex = i
                    }

                     qualityModel.existingQualityProfile = 1
                }

                // Set min available
                if (qualityItem.available && availableMin == -1)
                {
                    availableMin = i
                }

                // Set max available
                if (qualityItem.available)
                {
                    availableMax = i
                }
            }

            // Set total available ticks for active slider part
            if (availableMin != -1)
            {
                qualityModel.availableTotalTicks = availableMax - availableMin + 1
            }

            // Calculate slider values
            calculateSliderStepWidth(qualityModel.totalTicks)
            calculateSliderMargins(availableMin, availableMax, qualityModel.totalTicks)

            qualityModel.qualitySliderAvailableMin = availableMin
            qualityModel.qualitySliderAvailableMax = availableMax
        }

        function calculateSliderStepWidth (totalTicks)
        {
            // Do not use Math.round otherwise the tickmarks won't be aligned
            qualityModel.qualitySliderStepWidth = totalTicks != 0 ?
                    ((settingsColumnWidth - UM.Theme.getSize("print_setup_slider_handle").width) / (totalTicks)) : 0
        }

        function calculateSliderMargins (availableMin, availableMax, totalTicks)
        {
            if (availableMin == -1 || (availableMin == 0 && availableMax == 0))
            {
                // Do not use Math.round otherwise the tickmarks won't be aligned
                qualityModel.qualitySliderMarginRight = settingsColumnWidth / 2
            }
            else if (availableMin == availableMax)
            {
                // Do not use Math.round otherwise the tickmarks won't be aligned
                qualityModel.qualitySliderMarginRight = (totalTicks - availableMin) * qualitySliderStepWidth
            }
            else
            {
                // Do not use Math.round otherwise the tickmarks won't be aligned
                qualityModel.qualitySliderMarginRight = (totalTicks - availableMax) * qualitySliderStepWidth
            }
        }

        function reset () {
            qualityModel.clear()
            qualityModel.availableTotalTicks = 0
            qualityModel.existingQualityProfile = 0

            // check, the ticks count cannot be less than zero
            qualityModel.totalTicks = Math.max(0, Cura.QualityProfilesDropDownMenuModel.rowCount() - 1)
        }
    }

    // Here are the elements that are shown in the left column
    Item
    {
        id: titleRow
        width: labelColumnWidth
        height: childrenRect.height

        Cura.IconWithText
        {
            id: qualityRowTitle
            source: UM.Theme.getIcon("category_layer_height")
            text: catalog.i18nc("@label", "Layer Height")
            font: UM.Theme.getFont("medium")
            anchors.left: parent.left
            anchors.right: customisedSettings.left
        }

        UM.SimpleButton
        {
            id: customisedSettings

            visible: Cura.SimpleModeSettingsManager.isProfileCustomized || Cura.MachineManager.hasCustomQuality
            height: visible ? UM.Theme.getSize("print_setup_icon").height : 0
            width: height
            anchors
            {
                right: parent.right
                rightMargin: UM.Theme.getSize("default_margin").width
                leftMargin: UM.Theme.getSize("default_margin").width
                verticalCenter: parent.verticalCenter
            }

            color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button")
            iconSource: UM.Theme.getIcon("reset")

            onClicked:
            {
                // if the current profile is user-created, switch to a built-in quality
                Cura.MachineManager.resetToUseDefaultQuality()
            }
            onEntered:
            {
                var tooltipContent = catalog.i18nc("@tooltip","You have modified some profile settings. If you want to change these go to custom mode.")
                base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("thick_margin").width, 0),  tooltipContent)
            }
            onExited: base.hideTooltip()
        }
    }

    // Show titles for the each quality slider ticks
    Item
    {
        anchors.left: speedSlider.left
        anchors.top: speedSlider.bottom
        height: childrenRect.height

        Repeater
        {
            model: qualityModel

            Label
            {
                anchors.verticalCenter: parent.verticalCenter
                anchors.top: parent.top
                // The height has to be set manually, otherwise it's not automatically calculated in the repeater
                height: UM.Theme.getSize("default_margin").height
                color: (Cura.MachineManager.activeMachine != null && Cura.QualityProfilesDropDownMenuModel.getItem(index).available) ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                text:
                {
                    var result = ""
                    if(Cura.MachineManager.activeMachine != null)
                    {
                        result = Cura.QualityProfilesDropDownMenuModel.getItem(index).layer_height

                        if(result == undefined)
                        {
                            result = "";
                        }
                        else
                        {
                            result = Number(Math.round(result + "e+2") + "e-2"); //Round to 2 decimals. Javascript makes this difficult...
                            if (result == undefined || result != result) //Parse failure.
                            {
                                result = "";
                            }
                        }
                    }
                    return result
                }

                x:
                {
                    // Make sure the text aligns correctly with each tick
                    if (qualityModel.totalTicks == 0)
                    {
                        // If there is only one tick, align it centrally
                        return Math.round(((settingsColumnWidth) - width) / 2)
                    }
                    else if (index == 0)
                    {
                        return Math.round(settingsColumnWidth / qualityModel.totalTicks) * index
                    }
                    else if (index == qualityModel.totalTicks)
                    {
                        return Math.round(settingsColumnWidth / qualityModel.totalTicks) * index - width
                    }
                    else
                    {
                        return Math.round((settingsColumnWidth / qualityModel.totalTicks) * index - (width / 2))
                    }
                }
                font: UM.Theme.getFont("default")
            }
        }
    }

    // Print speed slider
    // Two sliders are created, one at the bottom with the unavailable qualities
    // and the other at the top with the available quality profiles and so the handle to select them.
    Item
    {
        id: speedSlider
        height: childrenRect.height

        anchors
        {
            left: titleRow.right
            right: parent.right
            verticalCenter: titleRow.verticalCenter
        }

        // Draw unavailable slider
        Slider
        {
            id: unavailableSlider

            width: parent.width
            height: qualitySlider.height // Same height as the slider that is on top
            updateValueWhileDragging : false
            tickmarksEnabled: true

            minimumValue: 0
            // maximumValue must be greater than minimumValue to be able to see the handle. While the value is strictly
            // speaking not always correct, it seems to have the correct behavior (switching from 0 available to 1 available)
            maximumValue: qualityModel.totalTicks
            stepSize: 1

            style: SliderStyle
            {
                //Draw Unvailable line
                groove: Item
                {
                    Rectangle
                    {
                        height: UM.Theme.getSize("print_setup_slider_groove").height
                        width: control.width - UM.Theme.getSize("print_setup_slider_handle").width
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.verticalCenter: parent.verticalCenter
                        color: UM.Theme.getColor("quality_slider_unavailable")
                    }
                }

                handle: Item {}

                tickmarks: Repeater
                {
                    id: qualityRepeater
                    model: qualityModel.totalTicks > 0 ? qualityModel : 0

                    Rectangle
                    {
                        color: Cura.QualityProfilesDropDownMenuModel.getItem(index).available ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                        implicitWidth: UM.Theme.getSize("print_setup_slider_tickmarks").width
                        implicitHeight: UM.Theme.getSize("print_setup_slider_tickmarks").height
                        anchors.verticalCenter: parent.verticalCenter

                        // Do not use Math.round otherwise the tickmarks won't be aligned
                        x: ((UM.Theme.getSize("print_setup_slider_handle").width / 2) - (implicitWidth / 2) + (qualityModel.qualitySliderStepWidth * index))
                        radius: Math.round(implicitWidth / 2)
                    }
                }
            }

            // Create a mouse area on top of the unavailable profiles to show a specific tooltip
            MouseArea
            {
                anchors.fill: parent
                hoverEnabled: true
                enabled: !Cura.MachineManager.hasCustomQuality
                onEntered:
                {
                    var tooltipContent = catalog.i18nc("@tooltip", "This quality profile is not available for your current material and nozzle configuration. Please change these to enable this quality profile.")
                    base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("thick_margin").width, customisedSettings.height), tooltipContent)
                }
                onExited: base.hideTooltip()
            }
        }

        // Draw available slider
        Slider
        {
            id: qualitySlider

            width: qualityModel.qualitySliderStepWidth * (qualityModel.availableTotalTicks - 1) + UM.Theme.getSize("print_setup_slider_handle").width
            height: UM.Theme.getSize("print_setup_slider_handle").height // The handle is the widest element of the slider
            enabled: qualityModel.totalTicks > 0 && !Cura.SimpleModeSettingsManager.isProfileCustomized
            visible: qualityModel.availableTotalTicks > 0
            updateValueWhileDragging : false

            anchors
            {
                right: parent.right
                rightMargin: qualityModel.qualitySliderMarginRight
            }

            minimumValue: qualityModel.qualitySliderAvailableMin >= 0 ? qualityModel.qualitySliderAvailableMin : 0
            // maximumValue must be greater than minimumValue to be able to see the handle. While the value is strictly
            // speaking not always correct, it seems to have the correct behavior (switching from 0 available to 1 available)
            maximumValue: qualityModel.qualitySliderAvailableMax >= 1 ? qualityModel.qualitySliderAvailableMax : 1
            stepSize: 1

            value: qualityModel.qualitySliderActiveIndex

            style: SliderStyle
            {
                // Draw Available line
                groove: Item
                {
                    Rectangle
                    {
                        height: UM.Theme.getSize("print_setup_slider_groove").height
                        width: control.width - UM.Theme.getSize("print_setup_slider_handle").width
                        anchors.verticalCenter: parent.verticalCenter

                        // Do not use Math.round otherwise the tickmarks won't be aligned
                        x: UM.Theme.getSize("print_setup_slider_handle").width / 2
                        color: UM.Theme.getColor("quality_slider_available")
                    }
                }

                handle: Rectangle
                {
                    id: qualityhandleButton
                    color: UM.Theme.getColor("primary")
                    implicitWidth: UM.Theme.getSize("print_setup_slider_handle").width
                    implicitHeight: implicitWidth
                    radius: Math.round(implicitWidth / 2)
                    visible: !Cura.SimpleModeSettingsManager.isProfileCustomized && !Cura.MachineManager.hasCustomQuality && qualityModel.existingQualityProfile
                }
            }

            onValueChanged:
            {
                // only change if an active machine is set and the slider is visible at all.
                if (Cura.MachineManager.activeMachine != null && visible)
                {
                    // prevent updating during view initializing. Trigger only if the value changed by user
                    if (qualitySlider.value != qualityModel.qualitySliderActiveIndex && qualityModel.qualitySliderActiveIndex != -1)
                    {
                        // start updating with short delay
                        qualitySliderChangeTimer.start()
                    }
                }
            }

            // This mouse area is only used to capture the onHover state and don't propagate it to the unavailable mouse area
            MouseArea
            {
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.NoButton
                enabled: !Cura.MachineManager.hasCustomQuality
            }
        }

        // This mouse area will only take the mouse events and show a tooltip when the profile in use is
        // a user created profile
        MouseArea
        {
            anchors.fill: parent
            hoverEnabled: true
            visible: Cura.MachineManager.hasCustomQuality

            onEntered:
            {
                var tooltipContent = catalog.i18nc("@tooltip", "A custom profile is currently active. To enable the quality slider, choose a default quality profile in Custom tab")
                base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("thick_margin").width, customisedSettings.height),  tooltipContent)
            }
            onExited: base.hideTooltip()
        }
    }
}