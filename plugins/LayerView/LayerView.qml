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
        id: sliderMinimumLayer
        width: UM.Theme.getSize("slider_layerview_size").width
        height: UM.Theme.getSize("slider_layerview_size").height
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("slider_layerview_margin").width * 0.2
        orientation: Qt.Vertical
        minimumValue: 0;
        maximumValue: UM.LayerView.numLayers-1;
        stepSize: 1

        property real pixelsPerStep: ((height - UM.Theme.getSize("slider_handle").height) / (maximumValue - minimumValue)) * stepSize;

        value: UM.LayerView.minimumLayer
        onValueChanged: {
            UM.LayerView.setMinimumLayer(value)
            if (value > UM.LayerView.currentLayer) {
                UM.LayerView.setCurrentLayer(value);
            }
        }

        style: UM.Theme.styles.slider;
    }

    Slider
    {
        id: slider
        width: UM.Theme.getSize("slider_layerview_size").width
        height: UM.Theme.getSize("slider_layerview_size").height
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("slider_layerview_margin").width * 0.8
        orientation: Qt.Vertical
        minimumValue: 0;
        maximumValue: UM.LayerView.numLayers;
        stepSize: 1

        property real pixelsPerStep: ((height - UM.Theme.getSize("slider_handle").height) / (maximumValue - minimumValue)) * stepSize;

        value: UM.LayerView.currentLayer
        onValueChanged: {
                UM.LayerView.setCurrentLayer(value);
                if (value < UM.LayerView.minimumLayer) {
                    UM.LayerView.setMinimumLayer(value);
                }
            }

        style: UM.Theme.styles.slider;

        Rectangle
        {
            x: parent.width + UM.Theme.getSize("slider_layerview_background").width / 2;
            y: parent.height - (parent.value * parent.pixelsPerStep) - UM.Theme.getSize("slider_handle").height * 1.25;

            height: UM.Theme.getSize("slider_handle").height + UM.Theme.getSize("default_margin").height
            width: valueLabel.width + UM.Theme.getSize("default_margin").width
            Behavior on height { NumberAnimation { duration: 50; } }

            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("slider_groove_border")
            color: UM.Theme.getColor("tool_panel_background")

            visible: UM.LayerView.layerActivity && Printer.platformActivity ? true : false

            TextField
            {
                id: valueLabel
                property string maxValue: slider.maximumValue + 1
                text: slider.value + 1
                horizontalAlignment: TextInput.AlignRight;
                onEditingFinished:
                {
                    // Ensure that the cursor is at the first position. On some systems the text isn't fully visible
                    // Seems to have to do something with different dpi densities that QML doesn't quite handle.
                    // Another option would be to increase the size even further, but that gives pretty ugly results.
                    cursorPosition = 0;
                    if(valueLabel.text != '')
                    {
                        slider.value = valueLabel.text - 1;
                    }
                }
                validator: IntValidator { bottom: 1; top: slider.maximumValue + 1; }

                anchors.left: parent.left;
                anchors.leftMargin: UM.Theme.getSize("default_margin").width / 2;
                anchors.verticalCenter: parent.verticalCenter;

                width: Math.max(UM.Theme.getSize("line").width * maxValue.length + 2, 20);
                style: TextFieldStyle
                {
                    textColor: UM.Theme.getColor("setting_control_text");
                    font: UM.Theme.getFont("default");
                    background: Item { }
                }
            }

            BusyIndicator
            {
                id: busyIndicator;
                anchors.left: parent.right;
                anchors.leftMargin: UM.Theme.getSize("default_margin").width / 2;
                anchors.verticalCenter: parent.verticalCenter;

                width: UM.Theme.getSize("slider_handle").height;
                height: width;

                running: UM.LayerView.busy;
                visible: UM.LayerView.busy;
            }
        }
    }

    Rectangle {
        id: slider_background
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

    Rectangle {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        anchors.top: slider_background.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: UM.Theme.getSize("slider_layerview_background").width * 3
        height: slider.height + UM.Theme.getSize("default_margin").height * 2
        color: UM.Theme.getColor("tool_panel_background");
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")

        ListModel  // matches LayerView.py
        {
            id: layerViewTypes
            ListElement {
                text: "Material color"
                type_id: 0
            }
            ListElement {
                text: "Line type"
                type_id: 1  // these ids match the switching in the shader
            }
        }

        ComboBox
        {
            id: layerTypeCombobox
            anchors.top: parent.top
            anchors.left: parent.left
            model: layerViewTypes
            visible: !UM.LayerView.compatibilityMode
            onActivated: {
                var type_id = layerViewTypes.get(index).type_id;
                UM.LayerView.setLayerViewType(type_id);
                if (type_id == 1) {
                    // Line type
                    UM.LayerView.enableLegend();
                } else {
                    UM.LayerView.disableLegend();
                }
            }
            onModelChanged: {
                currentIndex = UM.LayerView.getLayerViewType();
            }
        }

        Label
        {
            id: compatibilityModeLabel
            anchors.top: parent.top
            anchors.left: parent.left
            text: catalog.i18nc("@label","Compatibility mode")
            visible: UM.LayerView.compatibilityMode
        }

        ColumnLayout {
            id: view_settings
            anchors.top: UM.LayerView.compatibilityMode ? compatibilityModeLabel.bottom : layerTypeCombobox.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            CheckBox {
                checked: true
                onClicked: {
                    UM.LayerView.setExtruderOpacity(0, checked ? 1.0 : 0.0);
                }
                text: "Extruder 1"
                visible: !UM.LayerView.compatibilityMode && (UM.LayerView.extruderCount >= 1)
            }
            CheckBox {
                checked: true
                onClicked: {
                    UM.LayerView.setExtruderOpacity(1, checked ? 1.0 : 0.0);
                }
                text: "Extruder 2"
                visible: !UM.LayerView.compatibilityMode && (UM.LayerView.extruderCount >= 2)
            }
            CheckBox {
                checked: true
                onClicked: {
                    UM.LayerView.setExtruderOpacity(2, checked ? 1.0 : 0.0);
                }
                text: "Extruder 3"
                visible: !UM.LayerView.compatibilityMode && (UM.LayerView.etruderCount >= 3)
            }
            CheckBox {
                checked: true
                onClicked: {
                    UM.LayerView.setExtruderOpacity(3, checked ? 1.0 : 0.0);
                }
                text: "Extruder 4"
                visible: !UM.LayerView.compatibilityMode && (UM.LayerView.extruderCount >= 4)
            }
            Label {
                text: "Other extruders always visible"
                visible: !UM.LayerView.compatibilityMode && (UM.LayerView.extruderCount >= 5)
            }
            CheckBox {
                onClicked: {
                    UM.LayerView.setShowTravelMoves(checked ? 1 : 0);
                }
                text: "Show travel moves"
            }
            CheckBox {
                checked: true
                onClicked: {
                    UM.LayerView.setShowSupport(checked ? 1 : 0);
                }
                text: "Show support"
            }
            CheckBox {
                checked: true
                onClicked: {
                    UM.LayerView.setShowAdhesion(checked ? 1 : 0);
                }
                text: "Show adhesion"
            }
            CheckBox {
                checked: true
                onClicked: {
                    UM.LayerView.setShowSkin(checked ? 1 : 0);
                }
                text: "Show skin"
            }
            CheckBox {
                checked: true
                onClicked: {
                    UM.LayerView.setShowInfill(checked ? 1 : 0);
                }
                text: "Show infill"
            }
        }
    }
}
