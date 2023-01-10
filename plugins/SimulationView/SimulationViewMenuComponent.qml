// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura


Cura.ExpandableComponent
{
    id: base

    dragPreferencesNamePrefix: "view/colorscheme"

    contentHeaderTitle: catalog.i18nc("@label", "Color scheme")

    Connections
    {
        target: UM.Preferences
        function onPreferenceChanged(preference)
        {
            if (preference !== "view/only_show_top_layers" && preference !== "view/top_layer_count" && ! preference.match("layerview/"))
            {
                return;
            }

            layerTypeCombobox.currentIndex = UM.SimulationView.compatibilityMode ? 1 : UM.Preferences.getValue("layerview/layer_view_type")
            layerTypeCombobox.updateLegends(layerTypeCombobox.currentIndex)
            viewSettings.extruder_opacities = UM.Preferences.getValue("layerview/extruder_opacities").split("|")
            viewSettings.show_travel_moves = UM.Preferences.getValue("layerview/show_travel_moves")
            viewSettings.show_helpers = UM.Preferences.getValue("layerview/show_helpers")
            viewSettings.show_skin = UM.Preferences.getValue("layerview/show_skin")
            viewSettings.show_infill = UM.Preferences.getValue("layerview/show_infill")
            viewSettings.only_show_top_layers = UM.Preferences.getValue("view/only_show_top_layers")
            viewSettings.top_layer_count = UM.Preferences.getValue("view/top_layer_count")
        }
    }

    headerItem: Item
    {
        UM.Label
        {
            id: colorSchemeLabel
            text: catalog.i18nc("@label", "Color scheme")
            height: parent.height
            elide: Text.ElideRight
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("text_medium")
        }

        UM.Label
        {
            text: layerTypeCombobox.currentText
            anchors
            {
                left: colorSchemeLabel.right
                leftMargin: UM.Theme.getSize("default_margin").width
                right: parent.right
            }
            height: parent.height
            elide: Text.ElideRight
            font: UM.Theme.getFont("medium")
        }
    }

    contentItem: Column
    {
        id: viewSettings

        property var extruder_opacities: UM.Preferences.getValue("layerview/extruder_opacities").split("|")
        property bool show_travel_moves: UM.Preferences.getValue("layerview/show_travel_moves")
        property bool show_helpers: UM.Preferences.getValue("layerview/show_helpers")
        property bool show_skin: UM.Preferences.getValue("layerview/show_skin")
        property bool show_infill: UM.Preferences.getValue("layerview/show_infill")
        property bool show_starts: UM.Preferences.getValue("layerview/show_starts")

        // If we are in compatibility mode, we only show the "line type"
        property bool show_legend: UM.SimulationView.compatibilityMode ? true : UM.Preferences.getValue("layerview/layer_view_type") == 1
        property bool show_gradient: UM.SimulationView.compatibilityMode ? false : UM.Preferences.getValue("layerview/layer_view_type") == 2 || UM.Preferences.getValue("layerview/layer_view_type") == 3
        property bool show_feedrate_gradient: show_gradient && UM.Preferences.getValue("layerview/layer_view_type") == 2
        property bool show_thickness_gradient: show_gradient && UM.Preferences.getValue("layerview/layer_view_type") == 3
        property bool show_line_width_gradient: show_gradient && UM.Preferences.getValue("layerview/layer_view_type") == 4
        property bool show_flow_rate_gradient: show_gradient && UM.Preferences.getValue("layerview/layer_view_type") == 5
        property bool only_show_top_layers: UM.Preferences.getValue("view/only_show_top_layers")
        property int top_layer_count: UM.Preferences.getValue("view/top_layer_count")

        width: UM.Theme.getSize("layerview_menu_size").width - 2 * UM.Theme.getSize("default_margin").width
        height: implicitHeight

        spacing: UM.Theme.getSize("layerview_row_spacing").height

        // matches SimulationView.py
        ListModel
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
                type_id: 1
            })
            layerViewTypes.append({
                text: catalog.i18nc("@label:listbox", "Speed"),
                type_id: 2
            })
            layerViewTypes.append({
                text: catalog.i18nc("@label:listbox", "Layer Thickness"),
                type_id: 3  // these ids match the switching in the shader
            })
            layerViewTypes.append({
                text: catalog.i18nc("@label:listbox", "Line Width"),
                type_id: 4
            })
            layerViewTypes.append({
                text: catalog.i18nc("@label:listbox", "Flow"),
                type_id: 5
            })
        }

        Cura.ComboBox
        {
            id: layerTypeCombobox
            textRole: "text"
            valueRole: "type_id"
            width: parent.width
            implicitHeight: UM.Theme.getSize("setting_control").height
            model: layerViewTypes
            visible: !UM.SimulationView.compatibilityMode

            onActivated: (index) => {UM.Preferences.setValue("layerview/layer_view_type", index)}

            Component.onCompleted:
            {
                currentIndex = UM.SimulationView.compatibilityMode ? 1 : UM.Preferences.getValue("layerview/layer_view_type");
                updateLegends(currentIndex);
            }

            function updateLegends(type_id)
            {
                // Update the visibility of the legends.
                viewSettings.show_legend = UM.SimulationView.compatibilityMode || (type_id == 1);
                viewSettings.show_gradient = !UM.SimulationView.compatibilityMode &&
                  (type_id == 2 || type_id == 3 || type_id == 4 || type_id == 5) ;

                viewSettings.show_feedrate_gradient = viewSettings.show_gradient && (type_id == 2);
                viewSettings.show_thickness_gradient = viewSettings.show_gradient && (type_id == 3);
                viewSettings.show_line_width_gradient = viewSettings.show_gradient && (type_id == 4);
                viewSettings.show_flow_rate_gradient = viewSettings.show_gradient && (type_id == 5);
            }
        }

        UM.Label
        {
            id: compatibilityModeLabel
            text: catalog.i18nc("@label", "Compatibility Mode")
            visible: UM.SimulationView.compatibilityMode
            height: UM.Theme.getSize("layerview_row").height
            width: parent.width
        }

        Item  // Spacer
        {
            height: UM.Theme.getSize("narrow_margin").width
            width: width
        }

        Repeater
        {
            model: CuraApplication.getExtrudersModel()

            UM.CheckBox
            {
                id: extrudersModelCheckBox
                checked: viewSettings.extruder_opacities[index] > 0.5 || viewSettings.extruder_opacities[index] == undefined || viewSettings.extruder_opacities[index] == ""
                height: UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("default_lining").height
                width: parent.width
                visible: !UM.SimulationView.compatibilityMode

                onClicked:
                {
                    viewSettings.extruder_opacities[index] = checked ? 1.0 : 0.0
                    UM.Preferences.setValue("layerview/extruder_opacities", viewSettings.extruder_opacities.join("|"));
                }

                Rectangle
                {
                    id: swatch
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: extrudersModelCheckBox.right
                    width: UM.Theme.getSize("layerview_legend_size").width
                    height: UM.Theme.getSize("layerview_legend_size").height
                    color: model.color
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                }

                UM.Label
                {
                    text: model.name
                    elide: Text.ElideRight
                    color: UM.Theme.getColor("setting_control_text")
                    anchors
                    {
                        verticalCenter: parent.verticalCenter
                        left: extrudersModelCheckBox.left
                        right: extrudersModelCheckBox.right
                        leftMargin: UM.Theme.getSize("checkbox").width + Math.round(UM.Theme.getSize("default_margin").width / 2)
                        rightMargin: UM.Theme.getSize("default_margin").width * 2
                    }
                }
            }
        }

        Repeater
        {
            model: ListModel
            {
                id: typesLegendModel
                Component.onCompleted:
                {
                    typesLegendModel.append({
                        label: catalog.i18nc("@label", "Travels"),
                        initialValue: viewSettings.show_travel_moves,
                        preference: "layerview/show_travel_moves",
                        colorId:  "layerview_move_combing"
                    });
                    typesLegendModel.append({
                        label: catalog.i18nc("@label", "Helpers"),
                        initialValue: viewSettings.show_helpers,
                        preference: "layerview/show_helpers",
                        colorId:  "layerview_support"
                    });
                    typesLegendModel.append({
                        label: catalog.i18nc("@label", "Shell"),
                        initialValue: viewSettings.show_skin,
                        preference: "layerview/show_skin",
                        colorId:  "layerview_inset_0"
                    });
                    typesLegendModel.append({
                        label: catalog.i18nc("@label", "Infill"),
                        initialValue: viewSettings.show_infill,
                        preference: "layerview/show_infill",
                        colorId:  "layerview_infill"
                    });
                    if (! UM.SimulationView.compatibilityMode)
                    {
                        typesLegendModel.append({
                            label: catalog.i18nc("@label", "Starts"),
                            initialValue: viewSettings.show_starts,
                            preference: "layerview/show_starts",
                            colorId:  "layerview_starts"
                        });
                    }
                }
            }

            UM.CheckBox
            {
                id: legendModelCheckBox
                checked: model.initialValue
                onClicked: UM.Preferences.setValue(model.preference, checked)
                height: UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("default_lining").height
                width: parent.width

                Rectangle
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: legendModelCheckBox.right
                    width: UM.Theme.getSize("layerview_legend_size").width
                    height: UM.Theme.getSize("layerview_legend_size").height
                    color: UM.Theme.getColor(model.colorId)
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                    visible: viewSettings.show_legend
                }

                UM.Label
                {
                    text: label
                    elide: Text.ElideRight
                    color: UM.Theme.getColor("setting_control_text")
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: legendModelCheckBox.left
                    anchors.right: legendModelCheckBox.right
                    anchors.leftMargin: UM.Theme.getSize("checkbox").width + Math.round(UM.Theme.getSize("default_margin").width / 2)
                    anchors.rightMargin: UM.Theme.getSize("default_margin").width * 2
                }
            }
        }

        UM.CheckBox
        {
            checked: viewSettings.only_show_top_layers
            onClicked: UM.Preferences.setValue("view/only_show_top_layers", checked ? 1.0 : 0.0)
            text: catalog.i18nc("@label", "Only Show Top Layers")
            visible: UM.SimulationView.compatibilityMode
            width: parent.width
        }

        UM.CheckBox
        {
            checked: viewSettings.top_layer_count == 5
            onClicked: UM.Preferences.setValue("view/top_layer_count", checked ? 5 : 1)
            text: catalog.i18nc("@label", "Show 5 Detailed Layers On Top")
            width: parent.width
            visible: UM.SimulationView.compatibilityMode
        }

        Repeater
        {
            model: ListModel
            {
                id: typesLegendModelNoCheck
                Component.onCompleted:
                {
                    typesLegendModelNoCheck.append({
                        label: catalog.i18nc("@label", "Top / Bottom"),
                        colorId: "layerview_skin",
                    });
                    typesLegendModelNoCheck.append({
                        label: catalog.i18nc("@label", "Inner Wall"),
                        colorId: "layerview_inset_x",
                    });
                }
            }

            UM.Label
            {
                text: label
                visible: viewSettings.show_legend
                id: typesLegendModelLabel

                height: UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("default_lining").height
                width: parent.width
                color: UM.Theme.getColor("setting_control_text")
                Rectangle
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: typesLegendModelLabel.right

                    width: UM.Theme.getSize("layerview_legend_size").width
                    height: UM.Theme.getSize("layerview_legend_size").height

                    color: UM.Theme.getColor(model.colorId)

                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("lining")
                }
            }
        }

        // Text for the minimum, maximum and units for the feedrates and layer thickness
        Item
        {
            id: gradientLegend
            visible: viewSettings.show_gradient
            width: parent.width
            height: UM.Theme.getSize("layerview_row").height

            UM.Label //Minimum value.
            {
                text:
                {
                    if (UM.SimulationView.layerActivity && CuraApplication.platformActivity)
                    {
                        // Feedrate selected
                        if (UM.Preferences.getValue("layerview/layer_view_type") == 2)
                        {
                            return parseFloat(UM.SimulationView.minFeedrate).toFixed(2)
                        }
                        // Layer thickness selected
                        if (UM.Preferences.getValue("layerview/layer_view_type") == 3)
                        {
                            return parseFloat(UM.SimulationView.minThickness).toFixed(2)
                        }
                        // Line width selected
                        if(UM.Preferences.getValue("layerview/layer_view_type") == 4)
                        {
                            return parseFloat(UM.SimulationView.minLineWidth).toFixed(2);
                        }
                        // Flow Rate selected
                        if(UM.Preferences.getValue("layerview/layer_view_type") == 5)
                        {
                            return parseFloat(UM.SimulationView.minFlowRate).toFixed(2);
                        }

                    }
                    return catalog.i18nc("@label","min")
                }
                anchors.left: parent.left
            }

            UM.Label //Unit in the middle.
            {
                text:
                {
                    if (UM.SimulationView.layerActivity && CuraApplication.platformActivity)
                    {
                        // Feedrate selected
                        if (UM.Preferences.getValue("layerview/layer_view_type") == 2)
                        {
                            return "mm/s"
                        }
                        // Layer thickness selected
                        if (UM.Preferences.getValue("layerview/layer_view_type") == 3)
                        {
                            return "mm"
                        }
                        //Line width selected
                        if(UM.Preferences.getValue("layerview/layer_view_type") == 4)
                        {
                            return "mm"
                        }
                        // Flow Rate selected
                        if (UM.Preferences.getValue("layerview/layer_view_type") == 5)
                        {
                            return "mm³/s"
                        }
                    }
                    return ""
                }

                anchors.horizontalCenter: parent.horizontalCenter
                color: UM.Theme.getColor("setting_control_text")
            }

            UM.Label //Maximum value.
            {
                text: {
                    if (UM.SimulationView.layerActivity && CuraApplication.platformActivity)
                    {
                        // Feedrate selected
                        if (UM.Preferences.getValue("layerview/layer_view_type") == 2)
                        {
                            return parseFloat(UM.SimulationView.maxFeedrate).toFixed(2)
                        }
                        // Layer thickness selected
                        if (UM.Preferences.getValue("layerview/layer_view_type") == 3)
                        {
                            return parseFloat(UM.SimulationView.maxThickness).toFixed(2)
                        }
                        //Line width selected
                        if(UM.Preferences.getValue("layerview/layer_view_type") == 4)
                        {
                            return parseFloat(UM.SimulationView.maxLineWidth).toFixed(2);
                        }
                        // Flow rate selected
                        if(UM.Preferences.getValue("layerview/layer_view_type") == 5)
                        {
                            return parseFloat(UM.SimulationView.maxFlowRate).toFixed(2);
                        }
                    }
                    return catalog.i18nc("@label","max")
                }

                anchors.right: parent.right
                color: UM.Theme.getColor("setting_control_text")
            }
        }

        // Gradient colors for feedrate
        Rectangle
        {
            id: feedrateGradient
            visible: (
              viewSettings.show_feedrate_gradient ||
              viewSettings.show_line_width_gradient
            )
            anchors.left: parent.left
            anchors.right: parent.right
            height: Math.round(UM.Theme.getSize("layerview_row").height * 1.5)
            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("lining")

            gradient: Gradient
            {
                orientation: Gradient.Horizontal
                GradientStop
                {
                    position: 0.000
                    color: Qt.rgba(0, 0, 1, 1)
                }
                GradientStop
                {
                    position: 0.25
                    color: Qt.rgba(0.25, 1, 0, 1)
                }
                GradientStop
                {
                    position: 0.375
                    color: Qt.rgba(0.375, 0.5, 0, 1)
                }
                GradientStop
                {
                    position: 1.0
                    color: Qt.rgba(1, 0.5, 0, 1)
                }
            }
        }

        // Gradient colors for layer thickness (similar to parula colormap)
        Rectangle
        {
            id: thicknessGradient
            visible: (
              viewSettings.show_thickness_gradient
            )
            anchors.left: parent.left
            anchors.right: parent.right
            height: Math.round(UM.Theme.getSize("layerview_row").height * 1.5)
            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("lining")

            gradient: Gradient
            {
                orientation: Gradient.Horizontal
                GradientStop
                {
                    position: 0.000
                    color: Qt.rgba(0, 0, 0.5, 1)
                }
                GradientStop
                {
                    position: 0.25
                    color: Qt.rgba(0, 0.375, 0.75, 1)
                }
                GradientStop
                {
                    position: 0.5
                    color: Qt.rgba(0, 0.75, 0.5, 1)
                }
                GradientStop
                {
                    position: 0.75
                    color: Qt.rgba(1, 0.75, 0.25, 1)
                }
                GradientStop
                {
                    position: 1.0
                    color: Qt.rgba(1, 1, 0, 1)
                }
            }
        }

        // Gradient colors for flow (similar to jet colormap)
        Rectangle
        {
            id: jetGradient
            visible: (
              viewSettings.show_flow_rate_gradient
            )
            anchors.left: parent.left
            anchors.right: parent.right
            height: Math.round(UM.Theme.getSize("layerview_row").height * 1.5)
            border.width: UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("lining")

            gradient: Gradient
            {
                orientation: Gradient.Horizontal
                GradientStop
                {
                    position: 0.0
                    color: Qt.rgba(0, 0, 0.5, 1)
                }
                GradientStop
                {
                    position: 0.125
                    color: Qt.rgba(0, 0.0, 1.0, 1)
                }
                GradientStop
                {
                    position: 0.25
                    color: Qt.rgba(0, 0.5, 1.0, 1)
                }
                GradientStop
                {
                    position: 0.375
                    color: Qt.rgba(0.0, 1.0, 1.0, 1)
                }
                GradientStop
                {
                    position: 0.5
                    color: Qt.rgba(0.5, 1.0, 0.5, 1)
                }
                GradientStop
                {
                    position: 0.625
                    color: Qt.rgba(1.0, 1.0, 0.0, 1)
                }
                GradientStop
                {
                    position: 0.75
                    color: Qt.rgba(1.0, 0.5, 0, 1)
                }
                GradientStop
                {
                    position: 0.875
                    color: Qt.rgba(1.0, 0.0, 0, 1)
                }
                GradientStop
                {
                    position: 1.0
                    color: Qt.rgba(0.5, 0, 0, 1)
                }
            }
        }
    }

    FontMetrics
    {
        id: fontMetrics
        font: UM.Theme.getFont("default")
    }
}
