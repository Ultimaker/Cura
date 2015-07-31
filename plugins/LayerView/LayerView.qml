// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM

Item 
{
    width: 250
    height: 250

    Slider 
    {
        id: slider
        width: 10
        height: 250
        anchors.right : parent.right
        anchors.rightMargin: UM.Theme.sizes.slider_layerview_margin.width
        orientation: Qt.Vertical
        minimumValue: 0;
        maximumValue: UM.LayerView.numLayers;
        stepSize: 1

        value: UM.LayerView.currentLayer
        onValueChanged: UM.LayerView.setCurrentLayer(value)

        style: UM.Theme.styles.layerViewSlider
    }
    Rectangle {
        anchors.right: parent.right
        y: -UM.Theme.sizes.slider_layerview_background_extension.height
        z: slider.z - 1
        width: UM.Theme.sizes.button.width
        height: UM.Theme.sizes.slider_layerview_background_extension.height
        color: UM.Theme.colors.slider_text_background
    }
    UM.AngledCornerRectangle {
        anchors.right : parent.right
        anchors.verticalCenter: parent.verticalCenter
        z: slider.z - 1
        cornerSize: UM.Theme.sizes.default_margin.width;
        width: UM.Theme.sizes.slider_layerview_background.width
        height: slider.height + UM.Theme.sizes.default_margin.height * 2
        color: UM.Theme.colors.slider_text_background
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
