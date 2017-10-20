// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.4
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM
import Cura 1.0 as Cura

Item
{
    id: base
    width: {
        if (UM.LayerView.compatibilityMode) {
            return UM.Theme.getSize("layerview_menu_size_compatibility").width;
        } else {
            return UM.Theme.getSize("layerview_menu_size").width;
        }
    }
    height: {
        if (UM.LayerView.compatibilityMode) {
            return UM.Theme.getSize("layerview_menu_size_compatibility").height;
        } else if (UM.Preferences.getValue("layerview/layer_view_type") == 0) {
            return UM.Theme.getSize("layerview_menu_size_material_color_mode").height + UM.LayerView.extruderCount * (UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("layerview_row_spacing").height)
        } else {
            return UM.Theme.getSize("layerview_menu_size").height + UM.LayerView.extruderCount * (UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("layerview_row_spacing").height)
        }
    }

    property var buttonTarget: {
        if(parent != null)
        {
            var force_binding = parent.y; // ensure this gets reevaluated when the panel moves
            return base.mapFromItem(parent.parent, parent.buttonTarget.x, parent.buttonTarget.y)
        }
        return Qt.point(0,0)
    }

    visible: parent != null ? !parent.parent.monitoringPrint: true

    UM.PointingRectangle {
        id: layerViewMenu
        anchors.right: parent.right
        anchors.top: parent.top
        width: parent.width
        height: parent.height
        z: slider.z - 1
        color: UM.Theme.getColor("tool_panel_background")
        borderWidth: UM.Theme.getSize("default_lining").width
        borderColor: UM.Theme.getColor("lining")
        arrowSize: 0 // hide arrow until weird issue with first time rendering is fixed

        ColumnLayout {
            id: view_settings

            property var extruder_opacities: UM.Preferences.getValue("layerview/extruder_opacities").split("|")
            property bool show_travel_moves: UM.Preferences.getValue("layerview/show_travel_moves")
            property bool show_helpers: UM.Preferences.getValue("layerview/show_helpers")
            property bool show_skin: UM.Preferences.getValue("layerview/show_skin")
            property bool show_infill: UM.Preferences.getValue("layerview/show_infill")
            // if we are in compatibility mode, we only show the "line type"
            property bool show_legend: UM.LayerView.compatibilityMode ? 1 : UM.Preferences.getValue("layerview/layer_view_type") == 1
            property bool only_show_top_layers: UM.Preferences.getValue("view/only_show_top_layers")
            property int top_layer_count: UM.Preferences.getValue("view/top_layer_count")

            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("layerview_row_spacing").height
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width

            Label
            {
                id: layerViewTypesLabel
                anchors.left: parent.left
                text: catalog.i18nc("@label","Color scheme")
                font: UM.Theme.getFont("default");
                visible: !UM.LayerView.compatibilityMode
                Layout.fillWidth: true
                color: UM.Theme.getColor("setting_control_text")
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
                style: UM.Theme.styles.combobox
                anchors.right: parent.right
                anchors.rightMargin: 10 * screenScaleFactor

                onActivated:
                {
                    UM.Preferences.setValue("layerview/layer_view_type", index);
                }

                Component.onCompleted:
                {
                    currentIndex = UM.LayerView.compatibilityMode ? 1 : UM.Preferences.getValue("layerview/layer_view_type");
                    updateLegends(currentIndex);
                }

                function updateLegends(type_id)
                {
                    // update visibility of legends
                    view_settings.show_legend = UM.LayerView.compatibilityMode || (type_id == 1);
                }

            }

            Label
            {
                id: compatibilityModeLabel
                anchors.left: parent.left
                text: catalog.i18nc("@label","Compatibility Mode")
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
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
                    layerTypeCombobox.currentIndex = UM.LayerView.compatibilityMode ? 1 : UM.Preferences.getValue("layerview/layer_view_type");
                    layerTypeCombobox.updateLegends(layerTypeCombobox.currentIndex);
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
                model: Cura.ExtrudersModel{}
                CheckBox {
                    id: extrudersModelCheckBox
                    checked: view_settings.extruder_opacities[index] > 0.5 || view_settings.extruder_opacities[index] == undefined || view_settings.extruder_opacities[index] == ""
                    onClicked: {
                        view_settings.extruder_opacities[index] = checked ? 1.0 : 0.0
                        UM.Preferences.setValue("layerview/extruder_opacities", view_settings.extruder_opacities.join("|"));
                    }
                    visible: !UM.LayerView.compatibilityMode
                    enabled: index + 1 <= 4
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: extrudersModelCheckBox.right
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        width: UM.Theme.getSize("layerview_legend_size").width
                        height: UM.Theme.getSize("layerview_legend_size").height
                        color: model.color
                        radius: width / 2
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("lining")
                        visible: !view_settings.show_legend
                    }
                    Layout.fillWidth: true
                    Layout.preferredHeight: UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("default_lining").height
                    Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
                    style: UM.Theme.styles.checkbox
                    Label
                    {
                        text: model.name
                        elide: Text.ElideRight
                        color: UM.Theme.getColor("setting_control_text")
                        font: UM.Theme.getFont("default")
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: extrudersModelCheckBox.left;
                        anchors.right: extrudersModelCheckBox.right;
                        anchors.leftMargin: UM.Theme.getSize("checkbox").width + UM.Theme.getSize("default_margin").width /2
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width * 2
                    }
                }
            }

            Repeater {
                model: ListModel {
                    id: typesLegenModel
                    Component.onCompleted:
                    {
                        typesLegenModel.append({
                            label: catalog.i18nc("@label", "Show Travels"),
                            initialValue: view_settings.show_travel_moves,
                            preference: "layerview/show_travel_moves",
                            colorId:  "layerview_move_combing"
                        });
                        typesLegenModel.append({
                            label: catalog.i18nc("@label", "Show Helpers"),
                            initialValue: view_settings.show_helpers,
                            preference: "layerview/show_helpers",
                            colorId:  "layerview_support"
                        });
                        typesLegenModel.append({
                            label: catalog.i18nc("@label", "Show Shell"),
                            initialValue: view_settings.show_skin,
                            preference: "layerview/show_skin",
                            colorId:  "layerview_inset_0"
                        });
                        typesLegenModel.append({
                            label: catalog.i18nc("@label", "Show Infill"),
                            initialValue: view_settings.show_infill,
                            preference: "layerview/show_infill",
                            colorId:  "layerview_infill"
                        });
                    }
                }

                CheckBox {
                    id: legendModelCheckBox
                    checked: model.initialValue
                    onClicked: {
                        UM.Preferences.setValue(model.preference, checked);
                    }
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: legendModelCheckBox.right
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        width: UM.Theme.getSize("layerview_legend_size").width
                        height: UM.Theme.getSize("layerview_legend_size").height
                        color: UM.Theme.getColor(model.colorId)
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("lining")
                        visible: view_settings.show_legend
                    }
                    Layout.fillWidth: true
                    Layout.preferredHeight: UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("default_lining").height
                    Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
                    style: UM.Theme.styles.checkbox
                    Label
                    {
                        text: label
                        font: UM.Theme.getFont("default")
                        elide: Text.ElideRight
                        color: UM.Theme.getColor("setting_control_text")
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.left: legendModelCheckBox.left;
                        anchors.right: legendModelCheckBox.right;
                        anchors.leftMargin: UM.Theme.getSize("checkbox").width + UM.Theme.getSize("default_margin").width /2
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width * 2
                    }
                }
            }

            CheckBox {
                checked: view_settings.only_show_top_layers
                onClicked: {
                    UM.Preferences.setValue("view/only_show_top_layers", checked ? 1.0 : 0.0);
                }
                text: catalog.i18nc("@label", "Only Show Top Layers")
                visible: UM.LayerView.compatibilityMode
                style: UM.Theme.styles.checkbox
            }
            CheckBox {
                checked: view_settings.top_layer_count == 5
                onClicked: {
                    UM.Preferences.setValue("view/top_layer_count", checked ? 5 : 1);
                }
                text: catalog.i18nc("@label", "Show 5 Detailed Layers On Top")
                visible: UM.LayerView.compatibilityMode
                style: UM.Theme.styles.checkbox
            }

            Repeater {
                model: ListModel {
                    id: typesLegenModelNoCheck
                    Component.onCompleted:
                    {
                        typesLegenModelNoCheck.append({
                            label: catalog.i18nc("@label", "Top / Bottom"),
                            colorId: "layerview_skin",
                        });
                        typesLegenModelNoCheck.append({
                            label: catalog.i18nc("@label", "Inner Wall"),
                            colorId: "layerview_inset_x",
                        });
                    }
                }

                Label {
                    text: label
                    visible: view_settings.show_legend
                    id: typesLegendModelLabel
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: typesLegendModelLabel.right
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        width: UM.Theme.getSize("layerview_legend_size").width
                        height: UM.Theme.getSize("layerview_legend_size").height
                        color: UM.Theme.getColor(model.colorId)
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("lining")
                        visible: view_settings.show_legend
                    }
                    Layout.fillWidth: true
                    Layout.preferredHeight: UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("default_lining").height
                    Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
                    color: UM.Theme.getColor("setting_control_text")
                    font: UM.Theme.getFont("default")
                }
            }
        }

        LayerSlider {
            id: slider

            width: UM.Theme.getSize("slider_handle").width
            height: UM.Theme.getSize("layerview_menu_size").height

            anchors {
                top: parent.bottom
                topMargin: UM.Theme.getSize("slider_layerview_margin").height
                right: layerViewMenu.right
                rightMargin: UM.Theme.getSize("slider_layerview_margin").width
            }

            // custom properties
            upperValue: UM.LayerView.currentLayer
            lowerValue: UM.LayerView.minimumLayer
            maximumValue: UM.LayerView.numLayers
            handleSize: UM.Theme.getSize("slider_handle").width
            trackThickness: UM.Theme.getSize("slider_groove").width
            trackColor: UM.Theme.getColor("slider_groove")
            trackBorderColor: UM.Theme.getColor("slider_groove_border")
            upperHandleColor: UM.Theme.getColor("slider_handle")
            lowerHandleColor: UM.Theme.getColor("slider_handle")
            rangeHandleColor: UM.Theme.getColor("slider_groove_fill")
            handleLabelWidth: UM.Theme.getSize("slider_layerview_background").width
            layersVisible: UM.LayerView.layerActivity && CuraApplication.platformActivity ? true : false

            // update values when layer data changes
            Connections {
                target: UM.LayerView
                onMaxLayersChanged: slider.setUpperValue(UM.LayerView.currentLayer)
                onMinimumLayerChanged: slider.setLowerValue(UM.LayerView.minimumLayer)
                onCurrentLayerChanged: slider.setUpperValue(UM.LayerView.currentLayer)
            }

            // make sure the slider handlers show the correct value after switching views
            Component.onCompleted: {
                slider.setLowerValue(UM.LayerView.minimumLayer)
                slider.setUpperValue(UM.LayerView.currentLayer)
            }
        }
    }

    FontMetrics {
        id: fontMetrics
        font: UM.Theme.getFont("default")
    }
}
