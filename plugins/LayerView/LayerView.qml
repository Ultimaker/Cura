// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM

Item
{
    width: UM.Theme.getSize("layerview_menu_size").width
    height: {
        if (UM.LayerView.compatibilityMode) {
            return UM.Theme.getSize("layerview_menu_size").height
        } else {
            return UM.Theme.getSize("layerview_menu_size").height + UM.LayerView.extruderCount * (UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("layerview_row_spacing").height)
        }
    }

    Rectangle {
        id: layerViewMenu
        anchors.left: parent.left
        anchors.top: parent.top
        width: parent.width
        height: parent.height
        z: slider.z - 1
        color: UM.Theme.getColor("tool_panel_background")

        ColumnLayout {
            id: view_settings

            property bool extruder0_checked: UM.Preferences.getValue("layerview/extruder0_opacity") > 0.5
            property bool extruder1_checked: UM.Preferences.getValue("layerview/extruder1_opacity") > 0.5
            property bool extruder2_checked: UM.Preferences.getValue("layerview/extruder2_opacity") > 0.5
            property bool extruder3_checked: UM.Preferences.getValue("layerview/extruder3_opacity") > 0.5
            property var extruder_opacities: UM.Preferences.getValue("layerview/extruder_opacities").split("|")
            property bool show_travel_moves: UM.Preferences.getValue("layerview/show_travel_moves")
            property bool show_helpers: UM.Preferences.getValue("layerview/show_helpers")
            property bool show_skin: UM.Preferences.getValue("layerview/show_skin")
            property bool show_infill: UM.Preferences.getValue("layerview/show_infill")
            property bool show_legend: false
            property bool only_show_top_layers: UM.Preferences.getValue("view/only_show_top_layers")
            property int top_layer_count: UM.Preferences.getValue("view/only_show_top_layers")

            /*
                layerTypeCombobox.layer_view_type = UM.Preferences.getValue("layerview/layer_view_type");
                view_settings.extruder_opacities = UM.Preferences.getValue("layerview/extruder_opacities").split("|");
                view_settings.show_travel_moves = UM.Preferences.getValue("layerview/show_travel_moves");
                view_settings.show_support = UM.Preferences.getValue("layerview/show_support");
                view_settings.show_adhesion = UM.Preferences.getValue("layerview/show_adhesion");
                view_settings.show_skin = UM.Preferences.getValue("layerview/show_skin");
                view_settings.show_infill = UM.Preferences.getValue("layerview/show_infill");
                view_settings.only_show_top_layers = UM.Preferences.getValue("view/only_show_top_layers");
                view_settings.top_layer_count = UM.Preferences.getValue("view/top_layer_count");
            */

            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("layerview_row_spacing").height

            Label
            {
                id: layersLabel
                anchors.left: parent.left
                text: catalog.i18nc("@label","View Mode: Layers")
                font.bold: true
            }

            Label
            {
                id: spaceLabel
                anchors.left: parent.left
                text: " "
                font.pointSize: 0.5
            }

            Label
            {
                id: layerViewTypesLabel
                anchors.left: parent.left
                text: catalog.i18nc("@label","Color scheme")
                visible: !UM.LayerView.compatibilityMode
                Layout.fillWidth: true
            }

            ListModel  // matches LayerView.py
            {
                id: layerViewTypes
            }

            Component.onCompleted:
            {
                layerViewTypes.append({
                    text: catalog.i18nc("@label:listbox", "Material Color"),
                    type_id: 0
                })
                layerViewTypes.append({
                    text: catalog.i18nc("@label:listbox", "Line Type"),
                    type_id: 1  // these ids match the switching in the shader
                })
            }

            ComboBox
            {
                id: layerTypeCombobox
                anchors.left: parent.left
                Layout.fillWidth: true
                Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
                model: layerViewTypes
                visible: !UM.LayerView.compatibilityMode

                property int layer_view_type: UM.Preferences.getValue("layerview/layer_view_type")
                currentIndex: layer_view_type  // index matches type_id
                onActivated: {
                    // Combobox selection
                    var type_id = index;  // layerViewTypes.get(index).type_id;
                    UM.Preferences.setValue("layerview/layer_view_type", type_id);
                    updateLegend();
                }
                onModelChanged: {
                    updateLegend();
                }

                // Update visibility of legend.
                function updateLegend() {
                    var type_id = model.get(currentIndex).type_id;
                    if (UM.LayerView.compatibilityMode || (type_id == 1)) {
                        // Line type
                        view_settings.show_legend = true;
                    } else {
                        view_settings.show_legend = false;
                    }
                }
            }

            Label
            {
                id: compatibilityModeLabel
                anchors.left: parent.left
                text: catalog.i18nc("@label","Compatibility Mode")
                visible: UM.LayerView.compatibilityMode
                Layout.fillWidth: true
                Layout.preferredHeight: UM.Theme.getSize("layerview_row").height
                Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
            }

            Label
            {
                id: space2Label
                anchors.left: parent.left
                text: " "
                font.pointSize: 0.5
            }

            Connections {
                target: UM.Preferences
                onPreferenceChanged:
                {
                    layerTypeCombobox.layer_view_type = UM.Preferences.getValue("layerview/layer_view_type");
                    view_settings.extruder_opacities = UM.Preferences.getValue("layerview/extruder_opacities").split("|");
                    view_settings.show_travel_moves = UM.Preferences.getValue("layerview/show_travel_moves");
                    view_settings.show_helpers = UM.Preferences.getValue("layerview/show_helpers");
                    view_settings.show_skin = UM.Preferences.getValue("layerview/show_skin");
                    view_settings.show_infill = UM.Preferences.getValue("layerview/show_infill");
                    view_settings.only_show_top_layers = UM.Preferences.getValue("view/only_show_top_layers");
                    view_settings.top_layer_count = UM.Preferences.getValue("view/top_layer_count");
                }
            }

            Repeater {
                model: UM.LayerView.extruderCount
                CheckBox {
                    checked: view_settings.extruder_opacities[index] > 0.5 || view_settings.extruder_opacities[index] == undefined || view_settings.extruder_opacities[index] == ""
                    onClicked: {
                        view_settings.extruder_opacities[index] = checked ? 1.0 : 0.0
                        UM.Preferences.setValue("layerview/extruder_opacities", view_settings.extruder_opacities.join("|"));
                    }
                    text: catalog.i18nc("@label", "Extruder %1").arg(index + 1)
                    visible: !UM.LayerView.compatibilityMode
                    enabled: index + 1 <= 4
                    Layout.fillWidth: true
                    Layout.preferredHeight: UM.Theme.getSize("layerview_row").height
                    Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
                }
            }

            CheckBox {
                checked: view_settings.show_travel_moves
                onClicked: {
                    UM.Preferences.setValue("layerview/show_travel_moves", checked);
                }
                text: catalog.i18nc("@label", "Show Travels")
                Rectangle {
                    anchors.top: parent.top
                    anchors.topMargin: 2
                    anchors.right: parent.right
                    width: UM.Theme.getSize("layerview_legend_size").width
                    height: UM.Theme.getSize("layerview_legend_size").height
                    color: UM.Theme.getColor("layerview_move_combing")
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                    visible: view_settings.show_legend
                }
                Layout.fillWidth: true
                Layout.preferredHeight: UM.Theme.getSize("layerview_row").height
                Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
            }
            CheckBox {
                checked: view_settings.show_helpers
                onClicked: {
                    UM.Preferences.setValue("layerview/show_helpers", checked);
                }
                text: catalog.i18nc("@label", "Show Helpers")
                Rectangle {
                    anchors.top: parent.top
                    anchors.topMargin: 2
                    anchors.right: parent.right
                    width: UM.Theme.getSize("layerview_legend_size").width
                    height: UM.Theme.getSize("layerview_legend_size").height
                    color: UM.Theme.getColor("layerview_support")
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                    visible: view_settings.show_legend
                }
                Layout.fillWidth: true
                Layout.preferredHeight: UM.Theme.getSize("layerview_row").height
                Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
            }
            CheckBox {
                checked: view_settings.show_skin
                onClicked: {
                    UM.Preferences.setValue("layerview/show_skin", checked);
                }
                text: catalog.i18nc("@label", "Show Shell")
                Rectangle {
                    anchors.top: parent.top
                    anchors.topMargin: 2
                    anchors.right: parent.right
                    width: UM.Theme.getSize("layerview_legend_size").width
                    height: UM.Theme.getSize("layerview_legend_size").height
                    color: UM.Theme.getColor("layerview_inset_0")
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                    visible: view_settings.show_legend
                }
                Layout.fillWidth: true
                Layout.preferredHeight: UM.Theme.getSize("layerview_row").height
                Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
            }
            CheckBox {
                checked: view_settings.show_infill
                onClicked: {
                    UM.Preferences.setValue("layerview/show_infill", checked);
                }
                text: catalog.i18nc("@label", "Show Infill")
                Rectangle {
                    anchors.top: parent.top
                    anchors.topMargin: 2
                    anchors.right: parent.right
                    width: UM.Theme.getSize("layerview_legend_size").width
                    height: UM.Theme.getSize("layerview_legend_size").height
                    color: UM.Theme.getColor("layerview_infill")
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                    visible: view_settings.show_legend
                }
                Layout.fillWidth: true
                Layout.preferredHeight: UM.Theme.getSize("layerview_row").height
                Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
            }

            Label
            {
                id: topBottomLabel
                anchors.left: parent.left
                text: catalog.i18nc("@label","Top / Bottom")
                Rectangle {
                    anchors.top: parent.top
                    anchors.topMargin: 2
                    anchors.right: parent.right
                    width: UM.Theme.getSize("layerview_legend_size").width
                    height: UM.Theme.getSize("layerview_legend_size").height
                    color: UM.Theme.getColor("layerview_skin")
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                }
                Layout.fillWidth: true
                Layout.preferredHeight: UM.Theme.getSize("layerview_row").height
                Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
                visible: view_settings.show_legend
            }

            Label
            {
                id: innerWallLabel
                anchors.left: parent.left
                text: catalog.i18nc("@label","Inner Wall")
                Rectangle {
                    anchors.top: parent.top
                    anchors.topMargin: 2
                    anchors.right: parent.right
                    width: UM.Theme.getSize("layerview_legend_size").width
                    height: UM.Theme.getSize("layerview_legend_size").height
                    color: UM.Theme.getColor("layerview_inset_x")
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                    visible: view_settings.show_legend
                }
                Layout.fillWidth: true
                Layout.preferredHeight: UM.Theme.getSize("layerview_row").height
                Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
                visible: view_settings.show_legend
            }

        }

        Slider
        {
            id: sliderMinimumLayer
            width: UM.Theme.getSize("slider_layerview_size").width
            height: parent.height - 2*UM.Theme.getSize("slider_layerview_margin").height
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("slider_layerview_margin").height
            anchors.right: layerViewMenu.right
            anchors.rightMargin: UM.Theme.getSize("slider_layerview_margin").width * 0.8
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
            height: parent.height - 2*UM.Theme.getSize("slider_layerview_margin").height  //UM.Theme.getSize("slider_layerview_size").height
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("slider_layerview_margin").height
            anchors.right: layerViewMenu.right
            anchors.rightMargin: UM.Theme.getSize("slider_layerview_margin").width * 0.2
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
