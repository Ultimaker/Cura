// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura
import QtQuick.Layouts 1.3


//
// Infill
//
Item
{
    id: infillRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)

    // Create a binding to update the icon when the infill density changes
    Binding
    {
        target: infillRowTitle
        property: "source"
        value:
        {
            const infill_steps = parseInt(infillSteps.properties.value);
            if (infill_steps != 0)
            {
                return UM.Theme.getIcon("InfillGradual")
            }

            const density = parseInt(infillDensity.properties.value)
            if (density == 0)
            {
                return UM.Theme.getIcon("Infill0");
            }
            else if (density < 40)
            {
                return UM.Theme.getIcon("Infill3");
            }
            else if (density < 90)
            {
                return UM.Theme.getIcon("Infill2");
            }
            else
            {
                return UM.Theme.getIcon("Infill100");
            }
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
            const density = parseInt(infillDensity.properties.value)
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
        text: `${catalog.i18nc("@label", "Infill")} (%)`
        font: UM.Theme.getFont("medium")
        width: labelColumnWidth
        iconSize: UM.Theme.getSize("medium_button_icon").width
        tooltipText: catalog.i18nc("@label", "Gradual infill will gradually increase the amount of infill towards the top.")
    }

    RowLayout
    {
        id: infillSliderContainer
        height: childrenRect.height

        spacing: UM.Theme.getSize("default_margin").width

        anchors
        {
            left: infillRowTitle.right
            right: parent.right
            verticalCenter: infillRowTitle.verticalCenter
        }

        UM.Label { Layout.fillWidth: false; text: "0" }

        Slider
        {
            id: infillSlider
            Layout.fillWidth: true

            property var ignoreValueChange: false

            width: parent.width
            height: childrenRect.height

            from: 0; to: 100; stepSize: 1

            // disable slider when gradual support is enabled
            enabled: parseInt(infillSteps.properties.value) == 0

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
                color: UM.Theme.getColor("lining")

                Repeater
                {
                    id: repeater
                    anchors.fill: parent
                    model: 11

                    Rectangle
                    {
                        color: UM.Theme.getColor("lining")
                        implicitWidth: UM.Theme.getSize("print_setup_slider_tickmarks").width
                        implicitHeight: UM.Theme.getSize("print_setup_slider_tickmarks").height
                        anchors.verticalCenter: parent.verticalCenter

                        x: Math.round(backgroundLine.width / (repeater.count - 1) * index - width / 2)

                        radius: Math.round(width / 2)
                    }
                }
            }

            handle: Rectangle
            {
                id: handleButton
                x: infillSlider.leftPadding + infillSlider.visualPosition * (infillSlider.availableWidth - width)
                anchors.verticalCenter: parent.verticalCenter
                implicitWidth: UM.Theme.getSize("print_setup_slider_handle").width
                implicitHeight: UM.Theme.getSize("print_setup_slider_handle").height
                radius: Math.round(width / 2)
                color: UM.Theme.getColor("main_background")
                border.color: UM.Theme.getColor("primary")
                border.width: UM.Theme.getSize("wide_lining").height
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

        UM.Label { Layout.fillWidth: false; text: "100" }
    }

    //  Gradual Support Infill Checkbox
    UM.CheckBox
    {
        id: enableGradualInfillCheckBox
        property alias _hovered: enableGradualInfillMouseArea.containsMouse

        anchors.top: infillSliderContainer.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: infillSliderContainer.left

        text: catalog.i18nc("@label", "Gradual infill")
        enabled: recommendedPrintSetup.settingsEnabled
        visible: infillSteps.properties.enabled == "True"
        checked: parseInt(infillSteps.properties.value) > 0

        MouseArea
        {
            id: enableGradualInfillMouseArea

            anchors.fill: parent
            hoverEnabled: true
            enabled: true

            property var previousInfillDensity: parseInt(infillDensity.properties.value)

            onClicked:
            {
                // Set to 90% only when enabling gradual infill
                var newInfillDensity;
                if (parseInt(infillSteps.properties.value) == 0)
                {
                    previousInfillDensity = parseInt(infillDensity.properties.value)
                    newInfillDensity = 90
                } else {
                    newInfillDensity = previousInfillDensity
                }
                Cura.MachineManager.setSettingForAllExtruders("infill_sparse_density", "value", String(newInfillDensity))

                var infill_steps_value = 0
                if (parseInt(infillSteps.properties.value) == 0)
                {
                    infill_steps_value = 5
                }

                Cura.MachineManager.setSettingForAllExtruders("gradual_infill_steps", "value", infill_steps_value)
            }

            onEntered: base.showTooltip(enableGradualInfillCheckBox, Qt.point(-infillSliderContainer.x - UM.Theme.getSize("thick_margin").width, 0),
                    catalog.i18nc("@label", "Gradual infill will gradually increase the amount of infill towards the top."))

            onExited: base.hideTooltip()
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

    UM.SettingPropertyProvider
    {
        id: infillSteps
        containerStackId: Cura.MachineManager.activeStackId
        key: "gradual_infill_steps"
        watchedProperties: ["value", "enabled"]
        storeIndex: 0
    }
}
