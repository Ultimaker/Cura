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
        if (UM.SimulationView.compatibilityMode) {
            return UM.Theme.getSize("layerview_menu_size_compatibility").width;
        } else {
            return UM.Theme.getSize("layerview_menu_size").width;
        }
    }
    height: {
        if (viewSettings.collapsed) {
            if (UM.SimulationView.compatibilityMode) {
                return UM.Theme.getSize("layerview_menu_size_compatibility_collapsed").height;
            }
            return UM.Theme.getSize("layerview_menu_size_collapsed").height;
        } else if (UM.SimulationView.compatibilityMode) {
            return UM.Theme.getSize("layerview_menu_size_compatibility").height;
        } else if (UM.Preferences.getValue("layerview/layer_view_type") == 0) {
            return UM.Theme.getSize("layerview_menu_size_material_color_mode").height + UM.SimulationView.extruderCount * (UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("layerview_row_spacing").height)
        } else {
            return UM.Theme.getSize("layerview_menu_size").height + UM.SimulationView.extruderCount * (UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("layerview_row_spacing").height)
        }
    }
    Behavior on height { NumberAnimation { duration: 100 } }

    property var buttonTarget: {
        if(parent != null)
        {
            var force_binding = parent.y; // ensure this gets reevaluated when the panel moves
            return base.mapFromItem(parent.parent, parent.buttonTarget.x, parent.buttonTarget.y)
        }
        return Qt.point(0,0)
    }

    visible: parent != null ? !parent.parent.monitoringPrint: true

    Rectangle {
        id: layerViewMenu
        anchors.right: parent.right
        anchors.top: parent.top
        width: parent.width
        height: parent.height
        clip: true
        z: layerSlider.z - 1
        color: UM.Theme.getColor("tool_panel_background")
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")

        Button {
            id: collapseButton
            anchors.top: parent.top
            anchors.topMargin: Math.floor(UM.Theme.getSize("default_margin").height + (UM.Theme.getSize("layerview_row").height - UM.Theme.getSize("default_margin").height) / 2)
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width

            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height

            onClicked: viewSettings.collapsed = !viewSettings.collapsed

            style: ButtonStyle
            {
                background: UM.RecolorImage
                {
                    width: control.width
                    height: control.height
                    sourceSize.width: width
                    sourceSize.height: width
                    color:  UM.Theme.getColor("setting_control_text")
                    source: viewSettings.collapsed ? UM.Theme.getIcon("arrow_left") : UM.Theme.getIcon("arrow_bottom")
                }
                label: Label{ }
            }
        }

        ColumnLayout {
            id: viewSettings

            property bool collapsed: false
            property var extruder_opacities: UM.Preferences.getValue("layerview/extruder_opacities").split("|")
            property bool show_travel_moves: UM.Preferences.getValue("layerview/show_travel_moves")
            property bool show_helpers: UM.Preferences.getValue("layerview/show_helpers")
            property bool show_skin: UM.Preferences.getValue("layerview/show_skin")
            property bool show_infill: UM.Preferences.getValue("layerview/show_infill")
            // if we are in compatibility mode, we only show the "line type"
            property bool show_legend: UM.SimulationView.compatibilityMode ? true : UM.Preferences.getValue("layerview/layer_view_type") == 1
            property bool show_gradient: UM.SimulationView.compatibilityMode ? false : UM.Preferences.getValue("layerview/layer_view_type") == 2 || UM.Preferences.getValue("layerview/layer_view_type") == 3
            property bool show_feedrate_gradient: show_gradient && UM.Preferences.getValue("layerview/layer_view_type") == 2
            property bool show_thickness_gradient: show_gradient && UM.Preferences.getValue("layerview/layer_view_type") == 3
            property bool only_show_top_layers: UM.Preferences.getValue("view/only_show_top_layers")
            property int top_layer_count: UM.Preferences.getValue("view/top_layer_count")

            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("layerview_row_spacing").height

            Label
            {
                id: layerViewTypesLabel
                anchors.left: parent.left
                text: catalog.i18nc("@label","Color scheme")
                font: UM.Theme.getFont("default");
                visible: !UM.SimulationView.compatibilityMode
                Layout.fillWidth: true
                color: UM.Theme.getColor("setting_control_text")
            }

            ListModel  // matches SimulationView.py
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
                    text: catalog.i18nc("@label:listbox", "Feedrate"),
                    type_id: 2
                })
                layerViewTypes.append({
                    text: catalog.i18nc("@label:listbox", "Layer thickness"),
                    type_id: 3  // these ids match the switching in the shader
                })
            }

            ComboBox
            {
                id: layerTypeCombobox
                anchors.left: parent.left
                Layout.fillWidth: true
                Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
                model: layerViewTypes
                visible: !UM.SimulationView.compatibilityMode
                style: UM.Theme.styles.combobox
                anchors.right: parent.right

                onActivated:
                {
                    UM.Preferences.setValue("layerview/layer_view_type", index);
                }

                Component.onCompleted:
                {
                    currentIndex = UM.SimulationView.compatibilityMode ? 1 : UM.Preferences.getValue("layerview/layer_view_type");
                    updateLegends(currentIndex);
                }

                function updateLegends(type_id)
                {
                    // update visibility of legends
                    viewSettings.show_legend = UM.SimulationView.compatibilityMode || (type_id == 1);
                    viewSettings.show_gradient = !UM.SimulationView.compatibilityMode && (type_id == 2 || type_id == 3);
                    viewSettings.show_feedrate_gradient = viewSettings.show_gradient && (type_id == 2);
                    viewSettings.show_thickness_gradient = viewSettings.show_gradient && (type_id == 3);
                }

            }

            Label
            {
                id: compatibilityModeLabel
                anchors.left: parent.left
                text: catalog.i18nc("@label","Compatibility Mode")
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                visible: UM.SimulationView.compatibilityMode
                Layout.fillWidth: true
                Layout.preferredHeight: UM.Theme.getSize("layerview_row").height
                Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
            }

            Item
            {
                height: Math.floor(UM.Theme.getSize("default_margin").width / 2)
                width: width
            }

            Connections {
                target: UM.Preferences
                onPreferenceChanged:
                {
                    layerTypeCombobox.currentIndex = UM.SimulationView.compatibilityMode ? 1 : UM.Preferences.getValue("layerview/layer_view_type");
                    layerTypeCombobox.updateLegends(layerTypeCombobox.currentIndex);
                    playButton.pauseSimulation();
                    viewSettings.extruder_opacities = UM.Preferences.getValue("layerview/extruder_opacities").split("|");
                    viewSettings.show_travel_moves = UM.Preferences.getValue("layerview/show_travel_moves");
                    viewSettings.show_helpers = UM.Preferences.getValue("layerview/show_helpers");
                    viewSettings.show_skin = UM.Preferences.getValue("layerview/show_skin");
                    viewSettings.show_infill = UM.Preferences.getValue("layerview/show_infill");
                    viewSettings.only_show_top_layers = UM.Preferences.getValue("view/only_show_top_layers");
                    viewSettings.top_layer_count = UM.Preferences.getValue("view/top_layer_count");
                }
            }

            Repeater {
                model: Cura.ExtrudersModel{}
                CheckBox {
                    id: extrudersModelCheckBox
                    checked: viewSettings.extruder_opacities[index] > 0.5 || viewSettings.extruder_opacities[index] == undefined || viewSettings.extruder_opacities[index] == ""
                    onClicked: {
                        viewSettings.extruder_opacities[index] = checked ? 1.0 : 0.0
                        UM.Preferences.setValue("layerview/extruder_opacities", viewSettings.extruder_opacities.join("|"));
                    }
                    visible: !UM.SimulationView.compatibilityMode
                    enabled: index + 1 <= 4
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: extrudersModelCheckBox.right
                        width: UM.Theme.getSize("layerview_legend_size").width
                        height: UM.Theme.getSize("layerview_legend_size").height
                        color: model.color
                        radius: width / 2
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("lining")
                        visible: !viewSettings.show_legend & !viewSettings.show_gradient
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
                    id: typesLegendModel
                    Component.onCompleted:
                    {
                        typesLegendModel.append({
                            label: catalog.i18nc("@label", "Show Travels"),
                            initialValue: viewSettings.show_travel_moves,
                            preference: "layerview/show_travel_moves",
                            colorId:  "layerview_move_combing"
                        });
                        typesLegendModel.append({
                            label: catalog.i18nc("@label", "Show Helpers"),
                            initialValue: viewSettings.show_helpers,
                            preference: "layerview/show_helpers",
                            colorId:  "layerview_support"
                        });
                        typesLegendModel.append({
                            label: catalog.i18nc("@label", "Show Shell"),
                            initialValue: viewSettings.show_skin,
                            preference: "layerview/show_skin",
                            colorId:  "layerview_inset_0"
                        });
                        typesLegendModel.append({
                            label: catalog.i18nc("@label", "Show Infill"),
                            initialValue: viewSettings.show_infill,
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
                        width: UM.Theme.getSize("layerview_legend_size").width
                        height: UM.Theme.getSize("layerview_legend_size").height
                        color: UM.Theme.getColor(model.colorId)
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("lining")
                        visible: viewSettings.show_legend
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
                checked: viewSettings.only_show_top_layers
                onClicked: {
                    UM.Preferences.setValue("view/only_show_top_layers", checked ? 1.0 : 0.0);
                }
                text: catalog.i18nc("@label", "Only Show Top Layers")
                visible: UM.SimulationView.compatibilityMode
                style: UM.Theme.styles.checkbox
            }
            CheckBox {
                checked: viewSettings.top_layer_count == 5
                onClicked: {
                    UM.Preferences.setValue("view/top_layer_count", checked ? 5 : 1);
                }
                text: catalog.i18nc("@label", "Show 5 Detailed Layers On Top")
                visible: UM.SimulationView.compatibilityMode
                style: UM.Theme.styles.checkbox
            }

            Repeater {
                model: ListModel {
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

                Label {
                    text: label
                    visible: viewSettings.show_legend
                    id: typesLegendModelLabel
                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: typesLegendModelLabel.right
                        width: UM.Theme.getSize("layerview_legend_size").width
                        height: UM.Theme.getSize("layerview_legend_size").height
                        color: UM.Theme.getColor(model.colorId)
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: UM.Theme.getColor("lining")
                        visible: viewSettings.show_legend
                    }
                    Layout.fillWidth: true
                    Layout.preferredHeight: UM.Theme.getSize("layerview_row").height + UM.Theme.getSize("default_lining").height
                    Layout.preferredWidth: UM.Theme.getSize("layerview_row").width
                    color: UM.Theme.getColor("setting_control_text")
                    font: UM.Theme.getFont("default")
                }
            }

            // Text for the minimum, maximum and units for the feedrates and layer thickness
            Item {
                id: gradientLegend
                visible: viewSettings.show_gradient
                width: parent.width
                height: UM.Theme.getSize("layerview_row").height
                anchors {
                    topMargin: UM.Theme.getSize("slider_layerview_margin").height
                    horizontalCenter: parent.horizontalCenter
                }

                Label {
                    text: minText()
                    anchors.left: parent.left
                    color: UM.Theme.getColor("setting_control_text")
                    font: UM.Theme.getFont("default")

                    function minText() {
                        if (UM.SimulationView.layerActivity && CuraApplication.platformActivity) {
                            // Feedrate selected
                            if (UM.Preferences.getValue("layerview/layer_view_type") == 2) {
                                return parseFloat(UM.SimulationView.getMinFeedrate()).toFixed(2)
                            }
                            // Layer thickness selected
                            if (UM.Preferences.getValue("layerview/layer_view_type") == 3) {
                                return parseFloat(UM.SimulationView.getMinThickness()).toFixed(2)
                            }
                        }
                        return catalog.i18nc("@label","min")
                    }
                }

                Label {
                    text: unitsText()
                    anchors.horizontalCenter: parent.horizontalCenter
                    color: UM.Theme.getColor("setting_control_text")
                    font: UM.Theme.getFont("default")

                    function unitsText() {
                        if (UM.SimulationView.layerActivity && CuraApplication.platformActivity) {
                            // Feedrate selected
                            if (UM.Preferences.getValue("layerview/layer_view_type") == 2) {
                                return "mm/s"
                            }
                            // Layer thickness selected
                            if (UM.Preferences.getValue("layerview/layer_view_type") == 3) {
                                return "mm"
                            }
                        }
                        return ""
                    }
                }

                Label {
                    text: maxText()
                    anchors.right: parent.right
                    color: UM.Theme.getColor("setting_control_text")
                    font: UM.Theme.getFont("default")

                    function maxText() {
                        if (UM.SimulationView.layerActivity && CuraApplication.platformActivity) {
                            // Feedrate selected
                            if (UM.Preferences.getValue("layerview/layer_view_type") == 2) {
                                return parseFloat(UM.SimulationView.getMaxFeedrate()).toFixed(2)
                            }
                            // Layer thickness selected
                            if (UM.Preferences.getValue("layerview/layer_view_type") == 3) {
                                return parseFloat(UM.SimulationView.getMaxThickness()).toFixed(2)
                            }
                        }
                        return catalog.i18nc("@label","max")
                    }
                }
            }

            // Gradient colors for feedrate
            Rectangle { // In QML 5.9 can be changed by LinearGradient
                // Invert values because then the bar is rotated 90 degrees
                id: feedrateGradient
                visible: viewSettings.show_feedrate_gradient
                anchors.left: parent.right
                height: parent.width
                width: UM.Theme.getSize("layerview_row").height * 1.5
                border.width: UM.Theme.getSize("default_lining").width
                border.color: UM.Theme.getColor("lining")
                transform: Rotation {origin.x: 0; origin.y: 0; angle: 90}
                gradient: Gradient {
                    GradientStop {
                        position: 0.000
                        color: Qt.rgba(1, 0.5, 0, 1)
                    }
                    GradientStop {
                        position: 0.625
                        color: Qt.rgba(0.375, 0.5, 0, 1)
                    }
                    GradientStop {
                        position: 0.75
                        color: Qt.rgba(0.25, 1, 0, 1)
                    }
                    GradientStop {
                        position: 1.0
                        color: Qt.rgba(0, 0, 1, 1)
                    }
                }
            }

            // Gradient colors for layer thickness
            Rectangle { // In QML 5.9 can be changed by LinearGradient
                // Invert values because then the bar is rotated 90 degrees
                id: thicknessGradient
                visible: viewSettings.show_thickness_gradient
                anchors.left: parent.right
                height: parent.width
                width: UM.Theme.getSize("layerview_row").height * 1.5
                border.width: UM.Theme.getSize("default_lining").width
                border.color: UM.Theme.getColor("lining")
                transform: Rotation {origin.x: 0; origin.y: 0; angle: 90}
                gradient: Gradient {
                    GradientStop {
                        position: 0.000
                        color: Qt.rgba(1, 0, 0, 1)
                    }
                    GradientStop {
                        position: 0.25
                        color: Qt.rgba(0.5, 0.5, 0, 1)
                    }
                    GradientStop {
                        position: 0.5
                        color: Qt.rgba(0, 1, 0, 1)
                    }
                    GradientStop {
                        position: 0.75
                        color: Qt.rgba(0, 0.5, 0.5, 1)
                    }
                    GradientStop {
                        position: 1.0
                        color: Qt.rgba(0, 0, 1, 1)
                    }
                }
            }
        }
    }

    Item {
        id: slidersBox

        width: parent.width
        visible: UM.SimulationView.layerActivity && CuraApplication.platformActivity

        anchors {
            top: parent.bottom
            topMargin: UM.Theme.getSize("slider_layerview_margin").height
            left: parent.left
        }

        PathSlider {
            id: pathSlider

            height: UM.Theme.getSize("slider_handle").width
            anchors.left: playButton.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            visible: !UM.SimulationView.compatibilityMode

            // custom properties
            handleValue: UM.SimulationView.currentPath
            maximumValue: UM.SimulationView.numPaths
            handleSize: UM.Theme.getSize("slider_handle").width
            trackThickness: UM.Theme.getSize("slider_groove").width
            trackColor: UM.Theme.getColor("slider_groove")
            trackBorderColor: UM.Theme.getColor("slider_groove_border")
            handleColor: UM.Theme.getColor("slider_handle")
            handleActiveColor: UM.Theme.getColor("slider_handle_active")
            rangeColor: UM.Theme.getColor("slider_groove_fill")

            // update values when layer data changes
            Connections {
                target: UM.SimulationView
                onMaxPathsChanged: pathSlider.setHandleValue(UM.SimulationView.currentPath)
                onCurrentPathChanged: pathSlider.setHandleValue(UM.SimulationView.currentPath)
            }

            // make sure the slider handlers show the correct value after switching views
            Component.onCompleted: {
                pathSlider.setHandleValue(UM.SimulationView.currentPath)
            }
        }

        LayerSlider {
            id: layerSlider

            width: UM.Theme.getSize("slider_handle").width
            height: UM.Theme.getSize("layerview_menu_size").height

            anchors {
                top: !UM.SimulationView.compatibilityMode ? pathSlider.bottom : parent.top
                topMargin: !UM.SimulationView.compatibilityMode ? UM.Theme.getSize("default_margin").height : 0
                right: parent.right
                rightMargin: UM.Theme.getSize("slider_layerview_margin").width
            }

            // custom properties
            upperValue: UM.SimulationView.currentLayer
            lowerValue: UM.SimulationView.minimumLayer
            maximumValue: UM.SimulationView.numLayers
            handleSize: UM.Theme.getSize("slider_handle").width
            trackThickness: UM.Theme.getSize("slider_groove").width
            trackColor: UM.Theme.getColor("slider_groove")
            trackBorderColor: UM.Theme.getColor("slider_groove_border")
            upperHandleColor: UM.Theme.getColor("slider_handle")
            lowerHandleColor: UM.Theme.getColor("slider_handle")
            rangeHandleColor: UM.Theme.getColor("slider_groove_fill")
            handleActiveColor: UM.Theme.getColor("slider_handle_active")
            handleLabelWidth: UM.Theme.getSize("slider_layerview_background").width

            // update values when layer data changes
            Connections {
                target: UM.SimulationView
                onMaxLayersChanged: layerSlider.setUpperValue(UM.SimulationView.currentLayer)
                onMinimumLayerChanged: layerSlider.setLowerValue(UM.SimulationView.minimumLayer)
                onCurrentLayerChanged: layerSlider.setUpperValue(UM.SimulationView.currentLayer)
            }

            // make sure the slider handlers show the correct value after switching views
            Component.onCompleted: {
                layerSlider.setLowerValue(UM.SimulationView.minimumLayer)
                layerSlider.setUpperValue(UM.SimulationView.currentLayer)
            }
        }

        // Play simulation button
        Button {
            id: playButton
            iconSource: "./resources/simulation_resume.svg"
            style: UM.Theme.styles.small_tool_button
            visible: !UM.SimulationView.compatibilityMode
            anchors {
                verticalCenter: pathSlider.verticalCenter
            }

            property var status: 0  // indicates if it's stopped (0) or playing (1)

            onClicked: {
                switch(status) {
                    case 0: {
                        resumeSimulation()
                        break
                    }
                    case 1: {
                        pauseSimulation()
                        break
                    }
                }
            }

            function pauseSimulation() {
                UM.SimulationView.setSimulationRunning(false)
                iconSource = "./resources/simulation_resume.svg"
                simulationTimer.stop()
                status = 0
            }

            function resumeSimulation() {
                UM.SimulationView.setSimulationRunning(true)
                iconSource = "./resources/simulation_pause.svg"
                simulationTimer.start()
            }
        }

        Timer
        {
            id: simulationTimer
            interval: 100
            running: false
            repeat: true
            onTriggered: {
                var currentPath = UM.SimulationView.currentPath
                var numPaths = UM.SimulationView.numPaths
                var currentLayer = UM.SimulationView.currentLayer
                var numLayers = UM.SimulationView.numLayers
                // When the user plays the simulation, if the path slider is at the end of this layer, we start
                // the simulation at the beginning of the current layer.
                if (playButton.status == 0)
                {
                    if (currentPath >= numPaths)
                    {
                        UM.SimulationView.setCurrentPath(0)
                    }
                    else
                    {
                        UM.SimulationView.setCurrentPath(currentPath+1)
                    }
                }
                // If the simulation is already playing and we reach the end of a layer, then it automatically
                // starts at the beginning of the next layer.
                else
                {
                    if (currentPath >= numPaths)
                    {
                        // At the end of the model, the simulation stops
                        if (currentLayer >= numLayers)
                        {
                            playButton.pauseSimulation()
                        }
                        else
                        {
                            UM.SimulationView.setCurrentLayer(currentLayer+1)
                            UM.SimulationView.setCurrentPath(0)
                        }
                    }
                    else
                    {
                        UM.SimulationView.setCurrentPath(currentPath+1)
                    }
                }
                playButton.status = 1
            }
        }
    }

    FontMetrics {
        id: fontMetrics
        font: UM.Theme.getFont("default")
    }
}
