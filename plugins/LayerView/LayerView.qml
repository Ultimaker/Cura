// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM

Item 
{
    width: UM.Theme.getSize("button").width
    height: UM.Theme.getSize("slider_layerview_size").height

    Slider 
    {
        id: slider
        width: UM.Theme.getSize("slider_layerview_size").width
        height: UM.Theme.getSize("slider_layerview_size").height
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("slider_layerview_margin").width/2
        orientation: Qt.Vertical
        minimumValue: 0;
        maximumValue: UM.LayerView.numLayers;
        stepSize: 1

        value: UM.LayerView.currentLayer
        onValueChanged: UM.LayerView.setCurrentLayer(value)

        style: UM.Theme.styles.layerViewSlider
    }
    Rectangle {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        z: slider.z - 1
        width: UM.Theme.getSize("slider_layerview_background").width
        height: slider.height + UM.Theme.getSize("default_margin").height * 2
        color: UM.Theme.getColor("tool_panel_background");
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")

        MouseArea {
            id: sliderMouseArea
            property double manualStepSize: slider.maximumValue / 11
            anchors.fill: parent
            onWheel: {
                slider.value = wheel.angleDelta.y < 0 ? slider.value - sliderMouseArea.manualStepSize : slider.value + sliderMouseArea.manualStepSize
            }
        }
    }
}
