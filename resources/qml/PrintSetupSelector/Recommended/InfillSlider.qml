// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura
import QtQuick.Layouts 1.3

RowLayout
{
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

        width: parent.width

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

        UM.PointingRectangle
        {
            arrowSize: UM.Theme.getSize("button_tooltip_arrow").width
            width: childrenRect.width
            height: childrenRect.height
            target: Qt.point(handleButton.x + handleButton.width / 2, handleButton.y + handleButton.height / 2)
            x: handleButton.x - width / 2 + handleButton.width / 2
            y: handleButton.y - height - UM.Theme.getSize("button_tooltip_arrow").height - UM.Theme.getSize("narrow_margin").height
            color: UM.Theme.getColor("tooltip");

            UM.Label
            {
                text: `${infillSlider.value}%`
                horizontalAlignment: TextInput.AlignHCenter
                leftPadding: UM.Theme.getSize("narrow_margin").width
                rightPadding: UM.Theme.getSize("narrow_margin").width
                color: UM.Theme.getColor("tooltip_text");
            }
        }

        Connections
        {
            target: infillSlider
            function onValueChanged()
            {
                // Work around, the `infillDensity.properties.value` is initially `undefined`. As
                // `parseInt(infillDensity.properties.value)` is parsed as 0 and is initially set as
                // the slider value. By setting this 0 value an update is triggered setting the actual
                // infill value to 0.
                if (isNaN(parseInt(infillDensity.properties.value)))
                {
                    return;
                }

                // Don't update if the setting value, if the slider has the same value
                if (parseInt(infillDensity.properties.value) == infillSlider.value)
                {
                    return;
                }

                // Round the slider value to the nearest multiple of 10 (simulate step size of 10)
                const roundedSliderValue = Math.round(infillSlider.value / 10) * 10;

                // Update the slider value to represent the rounded value
                infillSlider.value = roundedSliderValue;

                Cura.MachineManager.setSettingForAllExtruders("infill_sparse_density", "value", roundedSliderValue)
                Cura.MachineManager.resetSettingForAllExtruders("infill_line_distance")
            }
        }
    }

    UM.Label { Layout.fillWidth: false; text: "100" }
}
