// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM

Item
{
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

            property var extruder_opacities: UM.Preferences.getValue("layerview/extruder_opacities").split("|")
            property bool show_travel_moves: UM.Preferences.getValue("layerview/show_travel_moves")
            property bool show_helpers: UM.Preferences.getValue("layerview/show_helpers")
            property bool show_skin: UM.Preferences.getValue("layerview/show_skin")
            property bool show_infill: UM.Preferences.getValue("layerview/show_infill")
            property bool show_legend: UM.LayerView.compatibilityMode || UM.Preferences.getValue("layerview/layer_view_type") == 1
            property bool only_show_top_layers: UM.Preferences.getValue("view/only_show_top_layers")
            property int top_layer_count: UM.Preferences.getValue("view/top_layer_count")

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
                    var type_id = index;
                    UM.Preferences.setValue("layerview/layer_view_type", type_id);
                    updateLegend(type_id);
                }
                onModelChanged: {
                    updateLegend(UM.Preferences.getValue("layerview/layer_view_type"));
                }

                // Update visibility of legend.
                function updateLegend(type_id) {
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

        Item
        {
            id: slider
            width: handleSize
            height: parent.height - 2*UM.Theme.getSize("slider_layerview_margin").height
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("slider_layerview_margin").height
            anchors.right: layerViewMenu.right
            anchors.rightMargin: UM.Theme.getSize("slider_layerview_margin").width

            property real handleSize: UM.Theme.getSize("slider_handle").width
            property real handleRadius: handleSize / 2
            property real minimumRangeHandleSize: UM.Theme.getSize("slider_handle").width / 2
            property real trackThickness: UM.Theme.getSize("slider_groove").width
            property real trackRadius: trackThickness / 2
            property real trackBorderWidth: UM.Theme.getSize("default_lining").width
            property color upperHandleColor: UM.Theme.getColor("slider_handle")
            property color lowerHandleColor: UM.Theme.getColor("slider_handle")
            property color rangeHandleColor: UM.Theme.getColor("slider_groove_fill")
            property color trackColor: UM.Theme.getColor("slider_groove")
            property color trackBorderColor: UM.Theme.getColor("slider_groove_border")

            property real maximumValue: UM.LayerView.numLayers
            property real minimumValue: 0
            property real minimumRange: 0
            property bool roundValues: true

            property var activeHandle: upperHandle
            property bool layersVisible: UM.LayerView.layerActivity && Printer.platformActivity ? true : false

            function getUpperValueFromHandle()
            {
                var result = upperHandle.y / (height - (2 * handleSize + minimumRangeHandleSize));
                result = maximumValue + result * (minimumValue - (maximumValue - minimumRange));
                result = roundValues ? Math.round(result) | 0 : result;
                return result;
            }

            function getLowerValueFromHandle()
            {
                var result = (lowerHandle.y - (handleSize + minimumRangeHandleSize)) / (height - (2 * handleSize + minimumRangeHandleSize));
                result = maximumValue - minimumRange + result * (minimumValue - (maximumValue - minimumRange));
                result = roundValues ? Math.round(result) : result;
                return result;
            }

            function setUpperValue(value)
            {
                var value = (value - maximumValue) / (minimumValue - maximumValue);
                var new_upper_y =  Math.round(value * (height - (2 * handleSize + minimumRangeHandleSize)));

                if(new_upper_y != upperHandle.y)
                {
                    upperHandle.y = new_upper_y;
                }
                rangeHandle.height = lowerHandle.y - (upperHandle.y + upperHandle.height);
            }

            function setLowerValue(value)
            {
                var value = (value - maximumValue) / (minimumValue - maximumValue);
                var new_lower_y =  Math.round((handleSize + minimumRangeHandleSize) + value * (height - (2 * handleSize + minimumRangeHandleSize)));

                if(new_lower_y != lowerHandle.y)
                {
                    lowerHandle.y = new_lower_y;
                }
                rangeHandle.height = lowerHandle.y - (upperHandle.y + upperHandle.height);
            }

            Connections
            {
                target: UM.LayerView
                onMinimumLayerChanged: slider.setLowerValue(UM.LayerView.minimumLayer)
                onCurrentLayerChanged: slider.setUpperValue(UM.LayerView.currentLayer)
            }

            Rectangle {
                width: parent.trackThickness
                height: parent.height - parent.handleSize
                radius: parent.trackRadius
                anchors.centerIn: parent
                color: parent.trackColor
                border.width: parent.trackBorderWidth;
                border.color: parent.trackBorderColor;
            }

            Item {
                id: rangeHandle
                y: upperHandle.y + upperHandle.height
                width: parent.handleSize
                height: parent.minimumRangeHandleSize
                anchors.horizontalCenter: parent.horizontalCenter

                visible: slider.layersVisible

                property real value: UM.LayerView.currentLayer
                function setValue(value)
                {
                    var range = upperHandle.value - lowerHandle.value;
                    value = Math.min(value, slider.maximumValue);
                    value = Math.max(value, slider.minimumValue + range);
                    UM.LayerView.setCurrentLayer(value);
                    UM.LayerView.setMinimumLayer(value - range);
                }

                Rectangle {
                    anchors.centerIn: parent
                    width: parent.parent.trackThickness - 2 * parent.parent.trackBorderWidth
                    height: parent.height + parent.parent.handleSize
                    color: parent.parent.rangeHandleColor
                }

                MouseArea {
                    anchors.fill: parent

                    drag.target: parent
                    drag.axis: Drag.YAxis
                    drag.minimumY: upperHandle.height
                    drag.maximumY: parent.parent.height - (parent.height + lowerHandle.height)

                    onPressed: parent.parent.activeHandle = rangeHandle
                    onPositionChanged:
                    {
                        upperHandle.y = parent.y - upperHandle.height
                        lowerHandle.y = parent.y + parent.height

                        var upper_value = slider.getUpperValueFromHandle();
                        var lower_value = upper_value - (upperHandle.value - lowerHandle.value);
                        UM.LayerView.setCurrentLayer(upper_value);
                        UM.LayerView.setMinimumLayer(lower_value);
                    }
                }
            }

            Rectangle {
                id: upperHandle
                y: parent.height - (parent.minimumRangeHandleSize + 2 * parent.handleSize)
                width: parent.handleSize
                height: parent.handleSize
                anchors.horizontalCenter: parent.horizontalCenter
                radius: parent.handleRadius
                color: parent.upperHandleColor

                visible: slider.layersVisible

                property real value: UM.LayerView.currentLayer
                function setValue(value)
                {
                    UM.LayerView.setCurrentLayer(value);
                }

                MouseArea {
                    anchors.fill: parent

                    drag.target: parent
                    drag.axis: Drag.YAxis
                    drag.minimumY: 0
                    drag.maximumY: parent.parent.height - (2 * parent.parent.handleSize + parent.parent.minimumRangeHandleSize)

                    onPressed: parent.parent.activeHandle = upperHandle
                    onPositionChanged:
                    {
                        if(lowerHandle.y - (upperHandle.y + upperHandle.height) < parent.parent.minimumRangeHandleSize)
                        {
                            lowerHandle.y = upperHandle.y + upperHandle.height + parent.parent.minimumRangeHandleSize;
                        }
                        rangeHandle.height = lowerHandle.y - (upperHandle.y + upperHandle.height);

                        UM.LayerView.setCurrentLayer(slider.getUpperValueFromHandle());
                    }
                }
            }

            Rectangle {
                id: lowerHandle
                y: parent.height - parent.handleSize
                width: parent.handleSize
                height: parent.handleSize
                anchors.horizontalCenter: parent.horizontalCenter
                radius: parent.handleRadius
                color: parent.lowerHandleColor

                visible: slider.layersVisible

                property real value: UM.LayerView.minimumLayer
                function setValue(value)
                {
                    UM.LayerView.setMinimumLayer(value);
                }

                MouseArea {
                    anchors.fill: parent

                    drag.target: parent
                    drag.axis: Drag.YAxis
                    drag.minimumY: upperHandle.height + parent.parent.minimumRangeHandleSize
                    drag.maximumY: parent.parent.height - parent.height

                    onPressed: parent.parent.activeHandle = lowerHandle
                    onPositionChanged:
                    {
                        if(lowerHandle.y - (upperHandle.y + upperHandle.height) < parent.parent.minimumRangeHandleSize)
                        {
                            upperHandle.y = lowerHandle.y - (upperHandle.height + parent.parent.minimumRangeHandleSize);
                        }
                        rangeHandle.height = lowerHandle.y - (upperHandle.y + upperHandle.height)

                        UM.LayerView.setMinimumLayer(slider.getLowerValueFromHandle());
                    }
                }
            }

            UM.PointingRectangle
            {
                x: parent.width + UM.Theme.getSize("slider_layerview_background").width / 2;
                y: Math.floor(slider.activeHandle.y + slider.activeHandle.height / 2 - height / 2);

                target: Qt.point(0, slider.activeHandle.y + slider.activeHandle.height / 2)
                arrowSize: UM.Theme.getSize("default_arrow").width

                height: (Math.floor(UM.Theme.getSize("slider_handle").height + UM.Theme.getSize("default_margin").height) / 2) * 2 // Make sure height has an integer middle so drawing a pointy border is easier
                width: valueLabel.width + UM.Theme.getSize("default_margin").width
                Behavior on height { NumberAnimation { duration: 50; } }

                color: UM.Theme.getColor("lining");

                visible: slider.layersVisible

                UM.PointingRectangle
                {
                    color: UM.Theme.getColor("tool_panel_background")
                    target: Qt.point(0, height / 2 + UM.Theme.getSize("default_lining").width)
                    arrowSize: UM.Theme.getSize("default_arrow").width
                    anchors.fill: parent
                    anchors.margins: UM.Theme.getSize("default_lining").width

                    MouseArea //Catch all mouse events (so scene doesnt handle them)
                    {
                        anchors.fill: parent
                    }
                }

                TextField
                {
                    id: valueLabel
                    property string maxValue: slider.maximumValue + 1
                    text: slider.activeHandle.value + 1
                    horizontalAlignment: TextInput.AlignRight;
                    onEditingFinished:
                    {
                        // Ensure that the cursor is at the first position. On some systems the text isn't fully visible
                        // Seems to have to do something with different dpi densities that QML doesn't quite handle.
                        // Another option would be to increase the size even further, but that gives pretty ugly results.
                        cursorPosition = 0;
                        if(valueLabel.text != '')
                        {
                            slider.activeHandle.setValue(valueLabel.text - 1);
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

                    Keys.onUpPressed: slider.activeHandle.setValue(slider.activeHandle.value + ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))
                    Keys.onDownPressed: slider.activeHandle.setValue(slider.activeHandle.value - ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))
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
    }
}
