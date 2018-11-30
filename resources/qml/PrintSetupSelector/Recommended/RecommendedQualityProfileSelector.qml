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
                    if (Cura.SimpleModeSettingsManager.isProfileUserCreated)
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
            qualityModel.qualitySliderStepWidth = totalTicks != 0 ? Math.round((settingsColumnWidth) / (totalTicks)) : 0
        }

        function calculateSliderMargins (availableMin, availableMax, totalTicks)
        {
            if (availableMin == -1 || (availableMin == 0 && availableMax == 0))
            {
                qualityModel.qualitySliderMarginRight = Math.round(settingsColumnWidth)
            }
            else if (availableMin == availableMax)
            {
                qualityModel.qualitySliderMarginRight = Math.round((totalTicks - availableMin) * qualitySliderStepWidth)
            }
            else
            {
                qualityModel.qualitySliderMarginRight = Math.round((totalTicks - availableMax) * qualitySliderStepWidth)
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

    Cura.IconWithText
    {
        id: qualityRowTitle
        source: UM.Theme.getIcon("category_layer_height")
        text: catalog.i18nc("@label", "Layer Height")
//        anchors.bottom: speedSlider.bottom
        width: labelColumnWidth
    }

    //Print speed slider
    Rectangle
    {
        id: speedSlider

        anchors
        {
            left: qualityRowTitle.right
            right: parent.right
        }

        color: "green"
        height: 20
    }
//
//    // Show titles for the each quality slider ticks
//    Item
//    {
//        anchors.left: speedSlider.left
//        anchors.top: speedSlider.bottom
//
//        Repeater
//        {
//            model: qualityModel
//
//            Label
//            {
//                anchors.verticalCenter: parent.verticalCenter
//                anchors.top: parent.top
//                color: (Cura.MachineManager.activeMachine != null && Cura.QualityProfilesDropDownMenuModel.getItem(index).available) ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
//                text:
//                {
//                    var result = ""
//                    if(Cura.MachineManager.activeMachine != null)
//                    {
//                        result = Cura.QualityProfilesDropDownMenuModel.getItem(index).layer_height
//
//                        if(result == undefined)
//                        {
//                            result = "";
//                        }
//                        else
//                        {
//                            result = Number(Math.round(result + "e+2") + "e-2"); //Round to 2 decimals. Javascript makes this difficult...
//                            if (result == undefined || result != result) //Parse failure.
//                            {
//                                result = "";
//                            }
//                        }
//                    }
//                    return result
//                }
//
//                x:
//                {
//                    // Make sure the text aligns correctly with each tick
//                    if (qualityModel.totalTicks == 0)
//                    {
//                        // If there is only one tick, align it centrally
//                        return Math.round(((settingsColumnWidth) - width) / 2)
//                    }
//                    else if (index == 0)
//                    {
//                        return Math.round(settingsColumnWidth / qualityModel.totalTicks) * index
//                    }
//                    else if (index == qualityModel.totalTicks)
//                    {
//                        return Math.round(settingsColumnWidth / qualityModel.totalTicks) * index - width
//                    }
//                    else
//                    {
//                        return Math.round((settingsColumnWidth / qualityModel.totalTicks) * index - (width / 2))
//                    }
//                }
//            }
//        }
//    }
//
//    //Print speed slider
//    Rectangle
//    {
//        id: speedSlider
//
//        anchors
//        {
//            left: qualityRowTitle.right
//            right: parent.right
//        }
//
//        // This Item is used only for tooltip, for slider area which is unavailable
////            Item
////            {
////                function showTooltip (showTooltip)
////                {
////                    if (showTooltip)
////                    {
////                        var content = catalog.i18nc("@tooltip", "This quality profile is not available for you current material and nozzle configuration. Please change these to enable this quality profile")
////                        base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("thick_margin").width, customisedSettings.height), content)
////                    }
////                    else
////                    {
////                        base.hideTooltip()
////                    }
////                }
////
////                id: unavailableLineToolTip
////                height: 20 * screenScaleFactor // hovered area height
////                z: parent.z + 1 // should be higher, otherwise the area can be hovered
////                x: 0
////                anchors.verticalCenter: qualitySlider.verticalCenter
////
////                Rectangle
////                {
////                    id: leftArea
////                    width:
////                    {
////                        if (qualityModel.availableTotalTicks == 0)
////                        {
////                            return qualityModel.qualitySliderStepWidth * qualityModel.totalTicks
////                        }
////                        return qualityModel.qualitySliderStepWidth * qualityModel.qualitySliderAvailableMin - 10
////                    }
////                    height: parent.height
////                    color: "transparent"
////
////                    MouseArea
////                    {
////                        anchors.fill: parent
////                        hoverEnabled: true
////                        enabled: Cura.SimpleModeSettingsManager.isProfileUserCreated == false
////                        onEntered: unavailableLineToolTip.showTooltip(true)
////                        onExited: unavailableLineToolTip.showTooltip(false)
////                    }
////                }
////
////                Item
////                {
////                    id: rightArea
////                    width:
////                    {
////                        if(qualityModel.availableTotalTicks == 0)
////                            return 0
////
////                        return qualityModel.qualitySliderMarginRight - 10
////                    }
////                    height: parent.height
////                    x:
////                    {
////                        if (qualityModel.availableTotalTicks == 0)
////                        {
////                            return 0
////                        }
////
////                        var leftUnavailableArea = qualityModel.qualitySliderStepWidth * qualityModel.qualitySliderAvailableMin
////                        var totalGap = qualityModel.qualitySliderStepWidth * (qualityModel.availableTotalTicks -1) + leftUnavailableArea + 10
////
////                        return totalGap
////                    }
////
////                    MouseArea
////                    {
////                        anchors.fill: parent
////                        hoverEnabled: true
////                        enabled: Cura.SimpleModeSettingsManager.isProfileUserCreated == false
////                        onEntered: unavailableLineToolTip.showTooltip(true)
////                        onExited: unavailableLineToolTip.showTooltip(false)
////                    }
////                }
////            }
//
//        // Draw Unavailable line
//        Rectangle
//        {
//            id: groovechildrect
//            width: parent.width
//            height: 2 * screenScaleFactor
//            color: UM.Theme.getColor("quality_slider_unavailable")
//            anchors.verticalCenter: qualitySlider.verticalCenter
//
//            // Draw ticks
//            Repeater
//            {
//                id: qualityRepeater
//                model: qualityModel.totalTicks > 0 ? qualityModel : 0
//
//                Rectangle
//                {
//                    color: Cura.QualityProfilesDropDownMenuModel.getItem(index).available ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
//                    implicitWidth: 4 * screenScaleFactor
//                    implicitHeight: implicitWidth
//                    anchors.verticalCenter: parent.verticalCenter
//                    x: Math.round(qualityModel.qualitySliderStepWidth * index)
//                    radius: Math.round(implicitWidth / 2)
//                }
//            }
//        }
//
//        // Draw available slider
//        Slider
//        {
//            id: qualitySlider
//            height: UM.Theme.getSize("thick_margin").height
//            anchors.bottom: parent.bottom
//            enabled: qualityModel.totalTicks > 0 && !Cura.SimpleModeSettingsManager.isProfileCustomized
//            visible: qualityModel.availableTotalTicks > 0
//            updateValueWhileDragging : false
//
//            minimumValue: qualityModel.qualitySliderAvailableMin >= 0 ? qualityModel.qualitySliderAvailableMin : 0
//            // maximumValue must be greater than minimumValue to be able to see the handle. While the value is strictly
//            // speaking not always correct, it seems to have the correct behavior (switching from 0 available to 1 available)
//            maximumValue: qualityModel.qualitySliderAvailableMax >= 1 ? qualityModel.qualitySliderAvailableMax : 1
//            stepSize: 1
//
//            value: qualityModel.qualitySliderActiveIndex
//
//            width: qualityModel.qualitySliderStepWidth * (qualityModel.availableTotalTicks - 1)
//
//            anchors.right: parent.right
//            anchors.rightMargin: qualityModel.qualitySliderMarginRight
//
//            style: SliderStyle
//            {
//                //Draw Available line
//                groove: Rectangle
//                {
//                    implicitHeight: 2 * screenScaleFactor
//                    color: UM.Theme.getColor("quality_slider_available")
//                    radius: Math.round(height / 2)
//                }
//
//                handle: Rectangle
//                {
//                    id: qualityhandleButton
//                    color: UM.Theme.getColor("quality_slider_available")
//                    implicitWidth: 12 * screenScaleFactor
//                    implicitHeight: implicitWidth
//                    radius: Math.round(implicitWidth / 2)
//                    visible: !Cura.SimpleModeSettingsManager.isProfileCustomized && !Cura.SimpleModeSettingsManager.isProfileUserCreated && qualityModel.existingQualityProfile
//                }
//            }
//
//            onValueChanged:
//            {
//                // only change if an active machine is set and the slider is visible at all.
//                if (Cura.MachineManager.activeMachine != null && visible)
//                {
//                    // prevent updating during view initializing. Trigger only if the value changed by user
//                    if (qualitySlider.value != qualityModel.qualitySliderActiveIndex && qualityModel.qualitySliderActiveIndex != -1)
//                    {
//                        // start updating with short delay
//                        qualitySliderChangeTimer.start()
//                    }
//                }
//            }
//        }
//
//        MouseArea
//        {
//            id: speedSliderMouseArea
//            anchors.fill: parent
//            hoverEnabled: true
//            enabled: Cura.SimpleModeSettingsManager.isProfileUserCreated
//
//            onEntered:
//            {
//                var content = catalog.i18nc("@tooltip", "A custom profile is currently active. To enable the quality slider, choose a default quality profile in Custom tab")
//                base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("thick_margin").width, customisedSettings.height),  content)
//            }
//            onExited: base.hideTooltip()
//        }
//    }
//
//    UM.SimpleButton
//    {
//        id: customisedSettings
//
//        visible: Cura.SimpleModeSettingsManager.isProfileCustomized || Cura.SimpleModeSettingsManager.isProfileUserCreated
//        height: Math.round(speedSlider.height * 0.8)
//        width: Math.round(speedSlider.height * 0.8)
//
//        anchors.verticalCenter: speedSlider.verticalCenter
//        anchors.right: speedSlider.left
//        anchors.rightMargin: Math.round(UM.Theme.getSize("thick_margin").width / 2)
//
//        color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button");
//        iconSource: UM.Theme.getIcon("reset");
//
//        onClicked:
//        {
//            // if the current profile is user-created, switch to a built-in quality
//            Cura.MachineManager.resetToUseDefaultQuality()
//        }
//        onEntered:
//        {
//            var content = catalog.i18nc("@tooltip","You have modified some profile settings. If you want to change these go to custom mode.")
//            base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("thick_margin").width, customisedSettings.height),  content)
//        }
//        onExited: base.hideTooltip()
//    }
}