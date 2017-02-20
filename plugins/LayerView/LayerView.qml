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
        }

        Component.onCompleted:
        {
            layerViewTypes.append({
                text: catalog.i18nc("@title:layerview mode", "Material Color"),
                type_id: 0
            })
            layerViewTypes.append({
                text: catalog.i18nc("@title:layerview mode", "Line Type"),
                type_id: 1  // these ids match the switching in the shader
            })
        }

        ComboBox
        {
            id: layerTypeCombobox
            anchors.top: parent.top
            anchors.left: parent.left
            model: layerViewTypes
            visible: !UM.LayerView.compatibilityMode
            property int layer_view_type: UM.Preferences.getValue("layerview/layer_view_type")
            currentIndex: layer_view_type  // index matches type_id
            onActivated: {
                // Combobox selection
                var type_id = layerViewTypes.get(index).type_id;
                UM.Preferences.setValue("layerview/layer_view_type", type_id);
                updateLegend();
            }
            onModelChanged: {
                updateLegend();
            }
            // Update visibility of legend.
            function updateLegend() {
                var type_id = layerViewTypes.get(currentIndex).type_id;
                if (UM.LayerView.compatibilityMode || (type_id == 1)) {
                    // Line type
                    UM.LayerView.enableLegend();
                } else {
                    UM.LayerView.disableLegend();
                }
            }
        }

        Label
        {
            id: compatibilityModeLabel
            anchors.top: parent.top
            anchors.left: parent.left
            text: catalog.i18nc("@label","Compatibility Mode")
            visible: UM.LayerView.compatibilityMode
        }

        Connections {
            target: UM.Preferences
            onPreferenceChanged:
            {
                layerTypeCombobox.layer_view_type = UM.Preferences.getValue("layerview/layer_view_type");
                view_settings.extruder_opacities = UM.Preferences.getValue("layerview/extruder_opacities").split(",");
                view_settings.show_travel_moves = UM.Preferences.getValue("layerview/show_travel_moves");
                view_settings.show_support = UM.Preferences.getValue("layerview/show_support");
                view_settings.show_adhesion = UM.Preferences.getValue("layerview/show_adhesion");
                view_settings.show_skin = UM.Preferences.getValue("layerview/show_skin");
                view_settings.show_infill = UM.Preferences.getValue("layerview/show_infill");
                view_settings.only_show_top_layers = UM.Preferences.getValue("view/only_show_top_layers");
                view_settings.top_layer_count = UM.Preferences.getValue("view/top_layer_count");
            }
        }

        ColumnLayout {
            id: view_settings

            property var extruder_opacities: UM.Preferences.getValue("layerview/extruder_opacities").split(",")
            property bool show_travel_moves: UM.Preferences.getValue("layerview/show_travel_moves")
            property bool show_support: UM.Preferences.getValue("layerview/show_support")
            property bool show_adhesion: UM.Preferences.getValue("layerview/show_adhesion")
            property bool show_skin: UM.Preferences.getValue("layerview/show_skin")
            property bool show_infill: UM.Preferences.getValue("layerview/show_infill")
            property bool only_show_top_layers: UM.Preferences.getValue("view/only_show_top_layers")
            property int top_layer_count: UM.Preferences.getValue("view/only_show_top_layers")

            anchors.top: UM.LayerView.compatibilityMode ? compatibilityModeLabel.bottom : layerTypeCombobox.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            Repeater {
                model: UM.LayerView.extruderCount
                CheckBox {
                    checked: [undefined, ""].indexOf(view_settings.extruder_opacities[index]) >= 0 || view_settings.extruder_opacities[index] > 0.5
                    onClicked: {
                        view_settings.extruder_opacities[index] = checked ? 1.0 : 0.0
                        UM.Preferences.setValue("layerview/extruder_opacities", view_settings.extruder_opacities.toString());
                    }
                    text: catalog.i18nc("@label", "Extruder %1").arg(index + 1)
                    visible: !UM.LayerView.compatibilityMode
                }
            }

            CheckBox {
                checked: view_settings.show_travel_moves
                onClicked: {
                    UM.Preferences.setValue("layerview/show_travel_moves", checked);
                }
                text: catalog.i18nc("@label", "Show Travel Moves")
            }
            CheckBox {
                checked: view_settings.show_support
                onClicked: {
                    UM.Preferences.setValue("layerview/show_support", checked);
                }
                text: catalog.i18nc("@label", "Show Support")
            }
            CheckBox {
                checked: view_settings.show_adhesion
                onClicked: {
                    UM.Preferences.setValue("layerview/show_adhesion", checked);
                }
                text: catalog.i18nc("@label", "Show Adhesion")
            }
            CheckBox {
                checked: view_settings.show_skin
                onClicked: {
                    UM.Preferences.setValue("layerview/show_skin", checked);
                }
                text: catalog.i18nc("@label", "Show Skin")
            }
            CheckBox {
                checked: view_settings.show_infill
                onClicked: {
                    UM.Preferences.setValue("layerview/show_infill", checked);
                }
                text: catalog.i18nc("@label", "Show Infill")
            }
            CheckBox {
                checked: view_settings.only_show_top_layers
                onClicked: {
                    UM.Preferences.setValue("view/only_show_top_layers", checked ? 1.0 : 0.0);
                }
                text: catalog.i18nc("@label", "Only Show Top Layers")
                visible: UM.LayerView.compatibilityMode
            }
            CheckBox {
                checked: view_settings.top_layer_count == 5
                onClicked: {
                    UM.Preferences.setValue("view/top_layer_count", checked ? 5 : 1);
                }
                text: catalog.i18nc("@label", "Show 5 Detailed Layers On Top")
                visible: UM.LayerView.compatibilityMode
            }
        }
    }
}
