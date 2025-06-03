// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: base

    signal showTooltip(Item item, point location, string text);
    signal hideTooltip();

    property Action configureSettings;
    property variant minimumPrintTime: PrintInformation.minimumPrintTime;
    property variant maximumPrintTime: PrintInformation.maximumPrintTime;
    property bool settingsEnabled: Cura.ExtruderManager.activeExtruderStackId || extrudersEnabledCount.properties.value == 1

    property bool isBlackBeltPrinter: Cura.MachineManager.activeDefinitionId == "blackbelt"

    Component.onCompleted: PrintInformation.enabled = true
    Component.onDestruction: PrintInformation.enabled = false
    UM.I18nCatalog { id: catalog; name: "cura" }

    ScrollView
    {
        visible: Cura.MachineManager.activeMachineName != "" // If no printers added then the view is invisible
        anchors.fill: parent
        style: UM.Theme.styles.scrollview
        flickableItem.flickableDirection: Flickable.VerticalFlick

        Rectangle
        {
            width: childrenRect.width
            height: childrenRect.height
            color: UM.Theme.getColor("sidebar")

            //
            // Quality profile
            //
            Item
            {
                id: qualityRow

                height: UM.Theme.getSize("sidebar_margin").height
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                anchors.right: parent.right

                Timer
                {
                    id: qualitySliderChangeTimer
                    interval: 50
                    running: false
                    repeat: false
                    onTriggered: {
                        if (isBlackBeltPrinter) {
                            currentLayerHeight.setPropertyValue("value", qualityModel.get(qualitySlider.value).layer_height)
                            return
                        }
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

                Connections
                {
                    target: Cura.MachineManager
                    onActiveVariantChanged:
                    {
                        var active_mode = UM.Preferences.getValue("cura/active_mode")

                        if (active_mode == 0 || active_mode == "simple") {
                            // if in simple mode, reset layer_height
                            currentLayerHeight.removeFromContainer(0);
                        }
                        qualityModel.update();
                    }
                }

                Connections {
                    target: base
                    onVisibleChanged:
                    {
                        // update needs to be called when the widgets are visible, otherwise the step width calculation
                        // will fail because the width of an invisible item is 0.
                        if (visible) {
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

                    function update () {
                        reset()

                        var availableMin = -1
                        var availableMax = -1

                        if (isBlackBeltPrinter)
                        {
                            qualityItem = {
                                "name": "",
                                "quality_type": "",
                                "layer_height": variantLayerHeight.properties.value,
                                "layer_height_unit": "mm",
                                "available": true,
                                "quality_group": ""
                            }
                            var availableMin = 0;
                            var availableMax = qualityModel.totalTicks;
                            var stepSize = 0.05;
                            if (variantLayerHeight.properties.value <= 0.1)
                            {
                                stepSize = 0.02;
                            }
                            for (var i = 0; i <= qualityModel.totalTicks; i++) {
                                var layer_height = Number(variantLayerHeight.properties.value) + stepSize * (i - (availableMax / 2))
                                if (Math.abs(layer_height - currentLayerHeight.properties.value) < stepSize / 2)
                                {
                                    qualityModel.qualitySliderActiveIndex = i;
                                    qualityModel.existingQualityProfile = 1
                                }
                                qualityItem["layer_height"] = layer_height;
                                qualityModel.append(qualityItem);
                            }

                            qualityModel.availableTotalTicks = qualityModel.totalTicks + 1

                            // Calculate slider values
                            calculateSliderStepWidth(qualityModel.totalTicks)
                            calculateSliderMargins(availableMin, availableMax, qualityModel.totalTicks)

                            qualityModel.qualitySliderAvailableMin = availableMin
                            qualityModel.qualitySliderAvailableMax = availableMax

                            return;
                        }

                        for (var i = 0; i < Cura.QualityProfilesDropDownMenuModel.rowCount(); i++) {
                            var qualityItem = Cura.QualityProfilesDropDownMenuModel.getItem(i)

                            // Add each quality item to the UI quality model
                            qualityModel.append(qualityItem)

                            // Set selected value
                            if (Cura.MachineManager.activeQualityType == qualityItem.quality_type) {
                                // set to -1 when switching to user created profile so all ticks are clickable
                                if (Cura.SimpleModeSettingsManager.isProfileUserCreated) {
                                    qualityModel.qualitySliderActiveIndex = -1
                                } else {
                                    qualityModel.qualitySliderActiveIndex = i
                                }

                                qualityModel.existingQualityProfile = 1
                            }

                            // Set min available
                            if (qualityItem.available && availableMin == -1) {
                                availableMin = i
                            }

                            // Set max available
                            if (qualityItem.available) {
                                availableMax = i
                            }
                        }

                        // Set total available ticks for active slider part
                        if (availableMin != -1) {
                            qualityModel.availableTotalTicks = availableMax - availableMin + 1
                        }

                        // Calculate slider values
                        calculateSliderStepWidth(qualityModel.totalTicks)
                        calculateSliderMargins(availableMin, availableMax, qualityModel.totalTicks)

                        qualityModel.qualitySliderAvailableMin = availableMin
                        qualityModel.qualitySliderAvailableMax = availableMax
                    }

                    function calculateSliderStepWidth (totalTicks) {
                        qualityModel.qualitySliderStepWidth = totalTicks != 0 ? Math.round((base.width * 0.55) / (totalTicks)) : 0
                    }

                    function calculateSliderMargins (availableMin, availableMax, totalTicks) {
                        if (availableMin == -1 || (availableMin == 0 && availableMax == 0)) {
                            qualityModel.qualitySliderMarginRight = Math.round(base.width * 0.55)
                        } else if (availableMin == availableMax) {
                            qualityModel.qualitySliderMarginRight = Math.round((totalTicks - availableMin) * qualitySliderStepWidth)
                        } else {
                            qualityModel.qualitySliderMarginRight = Math.round((totalTicks - availableMax) * qualitySliderStepWidth)
                        }
                    }

                    function reset () {
                        qualityModel.clear()
                        qualityModel.availableTotalTicks = 0
                        qualityModel.existingQualityProfile = 0

                        // check, the ticks count cannot be less than zero
                        if (isBlackBeltPrinter) {
                            qualityModel.totalTicks = 4; // includes 0
                            return
                        }
                        qualityModel.totalTicks = Math.max(0, Cura.QualityProfilesDropDownMenuModel.rowCount() - 1)
                    }
                }

                Label
                {
                    id: qualityRowTitle
                    text: catalog.i18nc("@label", "Layer Height")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                }

                // Show titles for the each quality slider ticks
                Item
                {
                    y: -5 * screenScaleFactor;
                    anchors.left: speedSlider.left
                    Repeater
                    {
                        model: qualityModel

                        Label
                        {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.top: parent.top
                            anchors.topMargin: Math.round(UM.Theme.getSize("sidebar_margin").height / 2)
                            color:
                            {
                                if(isBlackBeltPrinter)
                                {
                                    return UM.Theme.getColor("quality_slider_available")
                                }
                                return (Cura.MachineManager.activeMachine != null && Cura.QualityProfilesDropDownMenuModel.getItem(index).available) ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                            }
                            text:
                            {
                                var result = ""
                                if(isBlackBeltPrinter)
                                {
                                    return model.layer_height ? model.layer_height.toFixed(2) : ""
                                }
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

                            x: {
                                // Make sure the text aligns correctly with each tick
                                if (qualityModel.totalTicks == 0) {
                                    // If there is only one tick, align it centrally
                                    return Math.round(((base.width * 0.55) - width) / 2)
                                } else if (index == 0) {
                                    return Math.round(base.width * 0.55 / qualityModel.totalTicks) * index
                                } else if (index == qualityModel.totalTicks) {
                                    return Math.round(base.width * 0.55 / qualityModel.totalTicks) * index - width
                                } else {
                                    return Math.round((base.width * 0.55 / qualityModel.totalTicks) * index - (width / 2))
                                }
                            }
                        }
                    }
                }

                //Print speed slider
                Item
                {
                    id: speedSlider
                    width: Math.round(base.width * 0.55)
                    height: UM.Theme.getSize("sidebar_margin").height
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.topMargin: UM.Theme.getSize("sidebar_margin").height

                    // This Item is used only for tooltip, for slider area which is unavailable
                    Item
                    {
                        function showTooltip (showTooltip)
                        {
                            if (showTooltip)
                            {
                                var content = catalog.i18nc("@tooltip", "This quality profile is not available for you current material and nozzle configuration. Please change these to enable this quality profile")
                                base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("sidebar_margin").width, customisedSettings.height), content)
                            }
                            else
                            {
                                base.hideTooltip()
                            }
                        }

                        id: unavailableLineToolTip
                        height: 20 * screenScaleFactor // hovered area height
                        z: parent.z + 1 // should be higher, otherwise the area can be hovered
                        x: 0
                        anchors.verticalCenter: qualitySlider.verticalCenter

                        Rectangle
                        {
                            id: leftArea
                            width:
                            {
                                if (qualityModel.availableTotalTicks == 0)
                                {
                                    return qualityModel.qualitySliderStepWidth * qualityModel.totalTicks
                                }
                                return qualityModel.qualitySliderStepWidth * qualityModel.qualitySliderAvailableMin - 10
                            }
                            height: parent.height
                            color: "transparent"

                            MouseArea
                            {
                                anchors.fill: parent
                                hoverEnabled: true
                                enabled: Cura.SimpleModeSettingsManager.isProfileUserCreated == false
                                onEntered: unavailableLineToolTip.showTooltip(true)
                                onExited: unavailableLineToolTip.showTooltip(false)
                            }
                        }

                        Rectangle
                        {
                            id: rightArea
                            width: {
                                if(qualityModel.availableTotalTicks == 0)
                                    return 0

                                return qualityModel.qualitySliderMarginRight - 10
                            }
                            height: parent.height
                            color: "transparent"
                            x: {
                                if (qualityModel.availableTotalTicks == 0) {
                                    return 0
                                }

                                var leftUnavailableArea = qualityModel.qualitySliderStepWidth * qualityModel.qualitySliderAvailableMin
                                var totalGap = qualityModel.qualitySliderStepWidth * (qualityModel.availableTotalTicks -1) + leftUnavailableArea + 10

                                return totalGap
                            }

                            MouseArea {
                                anchors.fill: parent
                                hoverEnabled: true
                                enabled: Cura.SimpleModeSettingsManager.isProfileUserCreated == false
                                onEntered: unavailableLineToolTip.showTooltip(true)
                                onExited: unavailableLineToolTip.showTooltip(false)
                            }
                        }
                    }

                    // Draw Unavailable line
                    Rectangle
                    {
                        id: groovechildrect
                        width: Math.round(base.width * 0.55)
                        height: 2 * screenScaleFactor
                        color: UM.Theme.getColor("quality_slider_unavailable")
                        anchors.verticalCenter: qualitySlider.verticalCenter
                        x: 0
                    }

                    // Draw ticks
                    Repeater
                    {
                        id: qualityRepeater
                        model: qualityModel.totalTicks > 0 ? qualityModel : 0

                        Rectangle
                        {
                            anchors.verticalCenter: parent.verticalCenter
                            color:
                            {
                                if(isBlackBeltPrinter)
                                {
                                    return UM.Theme.getColor("quality_slider_available")
                                }
                                return Cura.QualityProfilesDropDownMenuModel.getItem(index).available ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                            }
                            width: 1 * screenScaleFactor
                            height: 6 * screenScaleFactor
                            y: 0
                            x: Math.round(qualityModel.qualitySliderStepWidth * index)
                        }
                    }

                    Slider
                    {
                        id: qualitySlider
                        height: UM.Theme.getSize("sidebar_margin").height
                        anchors.bottom: speedSlider.bottom
                        enabled:
                        {
                            if (isBlackBeltPrinter)
                            {
                                return true;
                            }
                            return qualityModel.totalTicks > 0 && !Cura.SimpleModeSettingsManager.isProfileCustomized
                        }
                        visible: qualityModel.availableTotalTicks > 0
                        updateValueWhileDragging : false

                        minimumValue: qualityModel.qualitySliderAvailableMin >= 0 ? qualityModel.qualitySliderAvailableMin : 0
                        // maximumValue must be greater than minimumValue to be able to see the handle. While the value is strictly
                        // speaking not always correct, it seems to have the correct behavior (switching from 0 available to 1 available)
                        maximumValue: qualityModel.qualitySliderAvailableMax >= 1 ? qualityModel.qualitySliderAvailableMax : 1
                        stepSize: 1

                        value: qualityModel.qualitySliderActiveIndex

                        width: qualityModel.qualitySliderStepWidth * (qualityModel.availableTotalTicks - 1)

                        anchors.right: parent.right
                        anchors.rightMargin: qualityModel.qualitySliderMarginRight

                        style: SliderStyle
                        {
                            //Draw Available line
                            groove: Rectangle {
                                implicitHeight: 2 * screenScaleFactor
                                color: UM.Theme.getColor("quality_slider_available")
                                radius: Math.round(height / 2)
                            }
                            handle: Item {
                                Rectangle {
                                    id: qualityhandleButton
                                    anchors.centerIn: parent
                                    color: UM.Theme.getColor("quality_slider_available")
                                    implicitWidth: 10 * screenScaleFactor
                                    implicitHeight: implicitWidth
                                    radius: Math.round(implicitWidth / 2)
                                    visible:
                                    {
                                        if (isBlackBeltPrinter)
                                        {
                                            return true
                                        }
                                        return !Cura.SimpleModeSettingsManager.isProfileCustomized && !Cura.SimpleModeSettingsManager.isProfileUserCreated && qualityModel.existingQualityProfile
                                    }
                                }
                            }
                        }

                        onValueChanged: {
                            // only change if an active machine is set and the slider is visible at all.
                            if (Cura.MachineManager.activeMachine != null && visible) {
                                // prevent updating during view initializing. Trigger only if the value changed by user
                                if (qualitySlider.value != qualityModel.qualitySliderActiveIndex && qualityModel.qualitySliderActiveIndex != -1) {
                                    // start updating with short delay
                                    qualitySliderChangeTimer.start()
                                }
                            }
                        }
                    }

                    MouseArea
                    {
                        id: speedSliderMouseArea
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: Cura.SimpleModeSettingsManager.isProfileUserCreated

                        onEntered:
                        {
                            var content = catalog.i18nc("@tooltip","A custom profile is currently active. To enable the quality slider, choose a default quality profile in Custom tab")
                            base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("sidebar_margin").width, customisedSettings.height),  content)
                        }
                        onExited:
                        {
                            base.hideTooltip();
                        }
                    }
                }

                Label
                {
                    id: speedLabel

                    anchors.top: speedSlider.bottom
                    anchors.left: parent.left

                    text: catalog.i18nc("@label", "Print Speed")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    width: Math.round(UM.Theme.getSize("sidebar").width * 0.35)
                    elide: Text.ElideRight
                }

                Label
                {
                    anchors.bottom: speedLabel.bottom
                    anchors.left: speedSlider.left

                    text: catalog.i18nc("@label", "Slower")
                    font: UM.Theme.getFont("default")
                    color: (qualityModel.availableTotalTicks > 1) ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                    horizontalAlignment: Text.AlignLeft
                }

                Label
                {
                    anchors.bottom: speedLabel.bottom
                    anchors.right: speedSlider.right

                    text: catalog.i18nc("@label", "Faster")
                    font: UM.Theme.getFont("default")
                    color: (qualityModel.availableTotalTicks > 1) ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                    horizontalAlignment: Text.AlignRight
                }

                UM.SimpleButton
                {
                    id: customisedSettings

                    visible: (Cura.SimpleModeSettingsManager.isProfileCustomized || Cura.SimpleModeSettingsManager.isProfileUserCreated) && !isBlackBeltPrinter
                    height: Math.round(speedSlider.height * 0.8)
                    width: Math.round(speedSlider.height * 0.8)

                    anchors.verticalCenter: speedSlider.verticalCenter
                    anchors.right: speedSlider.left
                    anchors.rightMargin: Math.round(UM.Theme.getSize("sidebar_margin").width / 2)

                    color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button");
                    iconSource: UM.Theme.getIcon("reset");

                    onClicked:
                    {
                        // if the current profile is user-created, switch to a built-in quality
                        Cura.MachineManager.resetToUseDefaultQuality()
                    }
                    onEntered:
                    {
                        var content = catalog.i18nc("@tooltip","You have modified some profile settings. If you want to change these go to custom mode.")
                        base.showTooltip(qualityRow, Qt.point(-UM.Theme.getSize("sidebar_margin").width, customisedSettings.height),  content)
                    }
                    onExited: base.hideTooltip()
                }
            }

            //
            // Infill
            //
            Item
            {
                id: infillCellLeft

                anchors.top: qualityRow.bottom
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height * 2
                anchors.left: parent.left

                width: Math.round(UM.Theme.getSize("sidebar").width * .45) - UM.Theme.getSize("sidebar_margin").width

                Label
                {
                    id: infillLabel
                    text: catalog.i18nc("@label", "Infill")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")

                    anchors.top: parent.top
                    anchors.topMargin: Math.round(UM.Theme.getSize("sidebar_margin").height * 1.7)
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                }
            }

            Item
            {
                id: infillCellRight

                height: infillSlider.height + UM.Theme.getSize("sidebar_margin").height + enableGradualInfillCheckBox.visible * (enableGradualInfillCheckBox.height + UM.Theme.getSize("sidebar_margin").height)
                width: Math.round(UM.Theme.getSize("sidebar").width * .55)

                anchors.left: infillCellLeft.right
                anchors.top: infillCellLeft.top
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height

                Label {
                    id: selectedInfillRateText

                    //anchors.top: parent.top
                    anchors.left: infillSlider.left
                    anchors.leftMargin: Math.round((infillSlider.value / infillSlider.stepSize) * (infillSlider.width / (infillSlider.maximumValue / infillSlider.stepSize)) - 10 * screenScaleFactor)
                    anchors.right: parent.right

                    text: parseInt(infillDensity.properties.value) + "%"
                    horizontalAlignment: Text.AlignLeft

                    color: infillSlider.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                }

                // We use a binding to make sure that after manually setting infillSlider.value it is still bound to the property provider
                Binding {
                    target: infillSlider
                    property: "value"
                    value: parseInt(infillDensity.properties.value)
                }

                Slider
                {
                    id: infillSlider

                    anchors.top: selectedInfillRateText.bottom
                    anchors.left: parent.left
                    anchors.right: infillIcon.left
                    anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width

                    height: UM.Theme.getSize("sidebar_margin").height
                    width: parseInt(infillCellRight.width - UM.Theme.getSize("sidebar_margin").width - style.handleWidth)

                    minimumValue: 0
                    maximumValue: 100
                    stepSize: 1
                    tickmarksEnabled: true

                    // disable slider when gradual support is enabled
                    enabled: parseInt(infillSteps.properties.value) == 0

                    // set initial value from stack
                    value: parseInt(infillDensity.properties.value)

                    onValueChanged: {

                        // Don't round the value if it's already the same
                        if (parseInt(infillDensity.properties.value) == infillSlider.value) {
                            return
                        }

                        // Round the slider value to the nearest multiple of 10 (simulate step size of 10)
                        var roundedSliderValue = Math.round(infillSlider.value / 10) * 10

                        // Update the slider value to represent the rounded value
                        infillSlider.value = roundedSliderValue

                        // Update value only if the Recomended mode is Active,
                        // Otherwise if I change the value in the Custom mode the Recomended view will try to repeat
                        // same operation
                        var active_mode = UM.Preferences.getValue("cura/active_mode")

                        if (active_mode == 0 || active_mode == "simple") {
                            Cura.MachineManager.setSettingForAllExtruders("infill_sparse_density", "value", roundedSliderValue)
                        }
                    }

                    style: SliderStyle
                    {
                        groove: Rectangle {
                            id: groove
                            implicitWidth: 200 * screenScaleFactor
                            implicitHeight: 2 * screenScaleFactor
                            color: control.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                            radius: 1
                        }

                        handle: Item {
                            Rectangle {
                                id: handleButton
                                anchors.centerIn: parent
                                color: control.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                                implicitWidth: 10 * screenScaleFactor
                                implicitHeight: 10 * screenScaleFactor
                                radius: 10 * screenScaleFactor
                            }
                        }

                        tickmarks: Repeater {
                            id: repeater
                            model: control.maximumValue / control.stepSize + 1

                            // check if a tick should be shown based on it's index and wether the infill density is a multiple of 10 (slider step size)
                            function shouldShowTick (index) {
                                if (index % 10 == 0) {
                                    return true
                                }
                                return false
                            }

                            Rectangle {
                                anchors.verticalCenter: parent.verticalCenter
                                color: control.enabled ? UM.Theme.getColor("quality_slider_available") : UM.Theme.getColor("quality_slider_unavailable")
                                width: 1 * screenScaleFactor
                                height: 6 * screenScaleFactor
                                y: 0
                                x: Math.round(styleData.handleWidth / 2 + index * ((repeater.width - styleData.handleWidth) / (repeater.count-1)))
                                visible: shouldShowTick(index)
                            }
                        }
                    }
                }

                Rectangle
                {
                    id: infillIcon

                    width: Math.round((parent.width / 5) - (UM.Theme.getSize("sidebar_margin").width))
                    height: width

                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.topMargin: Math.round(UM.Theme.getSize("sidebar_margin").height / 2)

                    // we loop over all density icons and only show the one that has the current density and steps
                    Repeater
                    {
                        id: infillIconList
                        model: infillModel
                        anchors.fill: parent

                        function activeIndex () {
                            for (var i = 0; i < infillModel.count; i++) {
                                var density = Math.round(infillDensity.properties.value)
                                var steps = Math.round(infillSteps.properties.value)
                                var infillModelItem = infillModel.get(i)

                                if (infillModelItem != "undefined"
                                    && density >= infillModelItem.percentageMin
                                    && density <= infillModelItem.percentageMax
                                    && steps >= infillModelItem.stepsMin
                                    && steps <= infillModelItem.stepsMax
                                ){
                                    return i
                                }
                            }
                            return -1
                        }

                        Rectangle
                        {
                            anchors.fill: parent
                            visible: infillIconList.activeIndex() == index

                            border.width: UM.Theme.getSize("default_lining").width
                            border.color: UM.Theme.getColor("quality_slider_unavailable")

                            UM.RecolorImage {
                                anchors.fill: parent
                                anchors.margins: 2 * screenScaleFactor
                                sourceSize.width: width
                                sourceSize.height: width
                                source: UM.Theme.getIcon(model.icon)
                                color: UM.Theme.getColor("quality_slider_unavailable")
                            }
                        }
                    }
                }

                //  Gradual Support Infill Checkbox
                CheckBox {
                    id: enableGradualInfillCheckBox
                    property alias _hovered: enableGradualInfillMouseArea.containsMouse

                    anchors.top: infillSlider.bottom
                    anchors.topMargin: Math.round(UM.Theme.getSize("sidebar_margin").height / 2) // closer to slider since it belongs to the same category
                    anchors.left: infillCellRight.left

                    style: UM.Theme.styles.checkbox
                    enabled: base.settingsEnabled
                    visible: infillSteps.properties.enabled == "True"
                    checked: parseInt(infillSteps.properties.value) > 0

                    MouseArea {
                        id: enableGradualInfillMouseArea

                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: true

                        property var previousInfillDensity: parseInt(infillDensity.properties.value)

                        onClicked: {
                            // Set to 90% only when enabling gradual infill
                            var newInfillDensity;
                            if (parseInt(infillSteps.properties.value) == 0) {
                                previousInfillDensity = parseInt(infillDensity.properties.value)
                                newInfillDensity = 90;
                            } else {
                                newInfillDensity = previousInfillDensity;
                            }
                            Cura.MachineManager.setSettingForAllExtruders("infill_sparse_density", "value", String(newInfillDensity))

                            var infill_steps_value = 0;
                            if (parseInt(infillSteps.properties.value) == 0)
                                infill_steps_value = 5;

                            Cura.MachineManager.setSettingForAllExtruders("gradual_infill_steps", "value", infill_steps_value)
                        }

                        onEntered: {
                            base.showTooltip(enableGradualInfillCheckBox, Qt.point(-infillCellRight.x, 0),
                                catalog.i18nc("@label", "Gradual infill will gradually increase the amount of infill towards the top."))
                        }

                        onExited: {
                            base.hideTooltip()
                        }
                    }

                    Label {
                        id: gradualInfillLabel
                        anchors.left: enableGradualInfillCheckBox.right
                        anchors.leftMargin: Math.round(UM.Theme.getSize("sidebar_margin").width / 2)
                        anchors.verticalCenter: enableGradualInfillCheckBox.verticalCenter
                        text: catalog.i18nc("@label", "Enable gradual")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                    }
                }

                //  Infill list model for mapping icon
                ListModel
                {
                    id: infillModel
                    Component.onCompleted:
                    {
                        infillModel.append({
                            percentageMin: -1,
                            percentageMax: 0,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "hollow"
                        })
                        infillModel.append({
                            percentageMin: 0,
                            percentageMax: 40,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "sparse"
                        })
                        infillModel.append({
                            percentageMin: 40,
                            percentageMax: 89,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "dense"
                        })
                        infillModel.append({
                            percentageMin: 90,
                            percentageMax: 9999999999,
                            stepsMin: -1,
                            stepsMax: 0,
                            icon: "solid"
                        })
                        infillModel.append({
                            percentageMin: 0,
                            percentageMax: 9999999999,
                            stepsMin: 1,
                            stepsMax: 9999999999,
                            icon: "gradual"
                        })
                    }
                }
            }

            //
            //  Enable support
            //
            Label
            {
                id: enableSupportLabel
                visible: enableSupportCheckBox.visible

                anchors.top: infillCellRight.bottom
                anchors.topMargin: Math.round(UM.Theme.getSize("sidebar_margin").height * 1.5)
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width
                anchors.right: infillCellLeft.right
                anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width
                anchors.verticalCenter: enableSupportCheckBox.verticalCenter

                text: catalog.i18nc("@label", "Generate Support");
                font: UM.Theme.getFont("default");
                color: UM.Theme.getColor("text");
                elide: Text.ElideRight
            }

            CheckBox
            {
                id: enableSupportCheckBox
                property alias _hovered: enableSupportMouseArea.containsMouse

                anchors.top: enableSupportLabel.top
                anchors.left: infillCellRight.left

                style: UM.Theme.styles.checkbox;
                enabled: base.settingsEnabled

                visible: supportEnabled.properties.enabled == "True"
                checked: supportEnabled.properties.value == "True";

                MouseArea
                {
                    id: enableSupportMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: true
                    onClicked:
                    {
                        // The value is a string "True" or "False"
                        supportEnabled.setPropertyValue("value", supportEnabled.properties.value != "True");
                    }
                    onEntered:
                    {
                        base.showTooltip(enableSupportCheckBox, Qt.point(-enableSupportCheckBox.x, 0),
                            catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, such parts would collapse during printing."));
                    }
                    onExited:
                    {
                        base.hideTooltip();
                    }
                }
            }

            ComboBox
            {
                id: supportExtruderCombobox
                visible: enableSupportCheckBox.visible && (supportEnabled.properties.value == "True") && (extrudersEnabledCount.properties.value > 1)
                model: extruderModel

                property string color_override: ""  // for manually setting values
                property string color:  // is evaluated automatically, but the first time is before extruderModel being filled
                {
                    var current_extruder = extruderModel.get(currentIndex);
                    color_override = "";
                    if (current_extruder === undefined) return ""
                    return (current_extruder.color) ? current_extruder.color : "";
                }

                textRole: "text"  // this solves that the combobox isn't populated in the first time Cura is started

                anchors.top: enableSupportCheckBox.top
                //anchors.topMargin: ((supportEnabled.properties.value === "True") && (machineExtruderCount.properties.value > 1)) ? UM.Theme.getSize("sidebar_margin").height : 0
                anchors.left: enableSupportCheckBox.right
                anchors.leftMargin: Math.round(UM.Theme.getSize("sidebar_margin").width / 2)

                width: Math.round(UM.Theme.getSize("sidebar").width * .55) - Math.round(UM.Theme.getSize("sidebar_margin").width / 2) - enableSupportCheckBox.width
                height: ((supportEnabled.properties.value == "True") && (machineExtruderCount.properties.value > 1)) ? UM.Theme.getSize("setting_control").height : 0

                Behavior on height { NumberAnimation { duration: 100 } }

                style: UM.Theme.styles.combobox_color
                enabled: base.settingsEnabled
                property alias _hovered: supportExtruderMouseArea.containsMouse

                currentIndex:
                {
                    if (supportExtruderNr.properties == null)
                    {
                        return Cura.MachineManager.defaultExtruderPosition;
                    }
                    else
                    {
                        var extruder = parseInt(supportExtruderNr.properties.value);
                        if ( extruder === -1)
                        {
                            return Cura.MachineManager.defaultExtruderPosition;
                        }
                        return extruder;
                    }
                }

                onActivated:
                {
                    // Send the extruder nr as a string.
                    supportExtruderNr.setPropertyValue("value", String(index));
                }
                MouseArea
                {
                    id: supportExtruderMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: base.settingsEnabled
                    acceptedButtons: Qt.NoButton
                    onEntered:
                    {
                        base.showTooltip(supportExtruderCombobox, Qt.point(-supportExtruderCombobox.x, 0),
                            catalog.i18nc("@label", "Select which extruder to use for support. This will build up supporting structures below the model to prevent the model from sagging or printing in mid air."));
                    }
                    onExited:
                    {
                        base.hideTooltip();
                    }
                }

                function updateCurrentColor()
                {
                    var current_extruder = extruderModel.get(currentIndex);
                    if (current_extruder !== undefined) {
                        supportExtruderCombobox.color_override = current_extruder.color;
                    }
                }

            }

            Label
            {
                id: adhesionHelperLabel
                visible: adhesionCheckBox.visible

                text: catalog.i18nc("@label", "Build Plate Adhesion")
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                elide: Text.ElideRight

                anchors {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("sidebar_margin").width
                    right: infillCellLeft.right
                    rightMargin: UM.Theme.getSize("sidebar_margin").width
                    verticalCenter: adhesionCheckBox.verticalCenter
                }
            }

            CheckBox
            {
                id: adhesionCheckBox
                property alias _hovered: adhesionMouseArea.containsMouse

                anchors.top: enableSupportCheckBox.visible ? enableSupportCheckBox.bottom : infillCellRight.bottom
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
                anchors.left: infillCellRight.left

                //: Setting enable printing build-plate adhesion helper checkbox
                style: UM.Theme.styles.checkbox;
                enabled: base.settingsEnabled

                visible: platformAdhesionType.properties.enabled == "True"
                checked: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none"

                MouseArea
                {
                    id: adhesionMouseArea
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: base.settingsEnabled
                    onClicked:
                    {
                        var adhesionType = "skirt";
                        if(!parent.checked)
                        {
                            // Remove the "user" setting to see if the rest of the stack prescribes a brim or a raft
                            platformAdhesionType.removeFromContainer(0);
                            adhesionType = platformAdhesionType.properties.value;
                            if(adhesionType == "skirt" || adhesionType == "none")
                            {
                                // If the rest of the stack doesn't prescribe an adhesion-type, default to a brim
                                adhesionType = "brim";
                            }
                        }
                        platformAdhesionType.setPropertyValue("value", adhesionType);
                    }
                    onEntered:
                    {
                        base.showTooltip(adhesionCheckBox, Qt.point(-adhesionCheckBox.x, 0),
                            catalog.i18nc("@label", "Enable printing a brim or raft. This will add a flat area around or under your object which is easy to cut off afterwards."));
                    }
                    onExited:
                    {
                        base.hideTooltip();
                    }
                }
            }

            Label
            {
                id: repetitionsLabel
                visible: repetitionsCount.visible

                text: catalog.i18nc("@label", "Number of copies")
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                elide: Text.ElideRight

                anchors {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("sidebar_margin").width
                    right: infillCellLeft.right
                    rightMargin: UM.Theme.getSize("sidebar_margin").width
                    verticalCenter: repetitionsCount.verticalCenter
                }
            }

            Rectangle
            {
                id: repetitionsCount
                visible: blackbeltRepetitions.properties.value > 0

                anchors.top:
                {
                    if (adhesionCheckBox.visible)
                    {
                        return adhesionCheckBox.bottom;
                    }
                    else if (enableSupportCheckBox.visible)
                    {
                        return enableSupportCheckBox.bottom;
                    }
                    return infillCellRight.bottom
                }
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
                anchors.left: infillCellRight.left

                width: UM.Theme.getSize("setting_control").width
                height: UM.Theme.getSize("setting_control").height

                border.width: Math.round(UM.Theme.getSize("default_lining").width)
                border.color:
                {
                    if(repetitionsCountMouseArea.containsMouse || repetitionsCountInput.activeFocus)
                    {
                        return UM.Theme.getColor("setting_control_border_highlight")
                    }
                    return UM.Theme.getColor("setting_control_border")
                }

                MouseArea
                {
                    id: repetitionsCountMouseArea
                    anchors.fill: parent;
                    hoverEnabled: true;
                    cursorShape: Qt.IBeamCursor
                }

                TextInput
                {
                    id: repetitionsCountInput

                    property string textBeforeEdit
                    property bool textHasChanged
                    onActiveFocusChanged:
                    {
                        if (activeFocus) {
                            textHasChanged = false;
                            textBeforeEdit = text;
                            selectAll();
                        }
                    }

                    Keys.onReleased:
                    {
                        if (text != textBeforeEdit)
                        {
                            textHasChanged = true;
                        }
                        if (textHasChanged && text != "" && parseInt(text) != 0)
                        {
                            blackbeltRepetitions.setPropertyValue("value", text)
                        }
                    }

                    color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")
                    font: UM.Theme.getFont("default")
                    renderType: Text.NativeRendering
                    anchors
                    {
                        left: parent.left
                        leftMargin: Math.round(UM.Theme.getSize("setting_unit_margin").width)
                        right: parent.right
                        rightMargin: Math.round(UM.Theme.getSize("setting_unit_margin").width)
                        verticalCenter: parent.verticalCenter
                    }

                    selectByMouse: true;

                    maximumLength: 3
                    clip: true  //Hide any text that exceeds the width of the text box.

                    validator: RegExpValidator { regExp: /^[1-9][0-9]*$/ }

                    Binding
                    {
                        target: repetitionsCountInput
                        property: "text"
                        value: blackbeltRepetitions.properties.value;
                        when: !repetitionsCountInput.activeFocus
                    }
                }
            }

            UM.SettingPropertyProvider
            {
                id: blackbeltRepetitions
                containerStackId: Cura.MachineManager.activeMachineId
                key: "blackbelt_repetitions"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: currentLayerHeight
                containerStackId: Cura.MachineManager.activeMachineId
                key: "layer_height"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.ContainerPropertyProvider
            {
                id: variantLayerHeight
                containerId: Cura.MachineManager.activeVariantId
                watchedProperties: [ "value" ]
                key: "layer_height"
            }

            ListModel
            {
                id: extruderModel
                Component.onCompleted: populateExtruderModel()
            }

            //: Model used to populate the extrudelModel
            Cura.ExtrudersModel
            {
                id: extruders
                onModelChanged: populateExtruderModel()
            }


            UM.SettingPropertyProvider
            {
                id: infillExtruderNumber
                containerStackId: Cura.MachineManager.activeStackId
                key: "infill_extruder_nr"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: infillDensity
                containerStackId: Cura.MachineManager.activeStackId
                key: "infill_sparse_density"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: infillSteps
                containerStackId: Cura.MachineManager.activeStackId
                key: "gradual_infill_steps"
                watchedProperties: ["value", "enabled"]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: platformAdhesionType
                containerStackId: Cura.MachineManager.activeMachineId
                key: "adhesion_type"
                watchedProperties: [ "value", "enabled" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: supportEnabled
                containerStackId: Cura.MachineManager.activeMachineId
                key: "support_enable"
                watchedProperties: [ "value", "enabled", "description" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: extrudersEnabledCount
                containerStackId: Cura.MachineManager.activeMachineId
                key: "extruders_enabled_count"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }

            UM.SettingPropertyProvider
            {
                id: supportExtruderNr
                containerStackId: Cura.MachineManager.activeMachineId
                key: "support_extruder_nr"
                watchedProperties: [ "value" ]
                storeIndex: 0
            }
        }
    }

    function populateExtruderModel()
    {
        extruderModel.clear();
        for(var extruderNumber = 0; extruderNumber < extruders.rowCount() ; extruderNumber++)
        {
            extruderModel.append({
                text: extruders.getItem(extruderNumber).name,
                color: extruders.getItem(extruderNumber).color
            })
        }
        supportExtruderCombobox.updateCurrentColor();
    }
}
