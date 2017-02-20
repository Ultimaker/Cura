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

    Item {
        id: slider

        width: handleSize
        height: UM.Theme.getSize("slider_layerview_size").height
        anchors.left: parent.left
        anchors.horizontalCenter: parent.horizontalCenter

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

        property real to: UM.LayerView.numLayers - 1
        property real from: 0
        property real minimumRange: 0
        property bool roundValues: true

        property real upper:
        {
            var result = upperHandle.y / (height - (2 * handleSize + minimumRangeHandleSize));
            result = to + result * (from - (to - minimumRange));
            result = roundValues ? Math.round(result) | 0 : result;
            return result;
        }
        property real lower:
        {
            var result = (lowerHandle.y - (handleSize + minimumRangeHandleSize)) / (height - (2 * handleSize + minimumRangeHandleSize));
            result = to - minimumRange + result * (from - (to - minimumRange));
            result = roundValues ? Math.round(result) : result;
            return result;
        }
        property real range: upper - lower
        property var activeHandle: upperHandle

        onLowerChanged:
        {
            UM.LayerView.setMinimumLayer(lower)
        }
        onUpperChanged:
        {
            UM.LayerView.setCurrentLayer(upper);
        }

        /*
        Component.onCompleted:
        {
            setLower(UM.LayerView.minimumLayer);
            setUpper(UM.LayerView.currentLayer);
        }
        */

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
            property real value: parent.upper

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
            property real value: parent.upper

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
            property real value: parent.lower

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
                }
            }
        }

        Rectangle
        {
            x: parent.width + UM.Theme.getSize("slider_layerview_background").width / 2;
            y: slider.activeHandle.y + slider.activeHandle.height / 2 - valueLabel.height / 2;

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
                text: "Material Color"
                type_id: 0
            }
            ListElement {
                text: "Line Type"
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
                view_settings.extruder0_checked = UM.Preferences.getValue("layerview/extruder0_opacity") > 0.5;
                view_settings.extruder1_checked = UM.Preferences.getValue("layerview/extruder1_opacity") > 0.5;
                view_settings.extruder2_checked = UM.Preferences.getValue("layerview/extruder2_opacity") > 0.5;
                view_settings.extruder3_checked = UM.Preferences.getValue("layerview/extruder3_opacity") > 0.5;
                view_settings.show_travel_moves = UM.Preferences.getValue("layerview/show_travel_moves");
                view_settings.show_support = UM.Preferences.getValue("layerview/show_support");
                view_settings.show_adhesion = UM.Preferences.getValue("layerview/show_adhesion");
                view_settings.show_skin = UM.Preferences.getValue("layerview/show_skin");
                view_settings.show_infill = UM.Preferences.getValue("layerview/show_infill");
            }
        }

        ColumnLayout {
            id: view_settings

            property bool extruder0_checked: UM.Preferences.getValue("layerview/extruder0_opacity") > 0.5
            property bool extruder1_checked: UM.Preferences.getValue("layerview/extruder1_opacity") > 0.5
            property bool extruder2_checked: UM.Preferences.getValue("layerview/extruder2_opacity") > 0.5
            property bool extruder3_checked: UM.Preferences.getValue("layerview/extruder3_opacity") > 0.5
            property bool show_travel_moves: UM.Preferences.getValue("layerview/show_travel_moves")
            property bool show_support: UM.Preferences.getValue("layerview/show_support")
            property bool show_adhesion: UM.Preferences.getValue("layerview/show_adhesion")
            property bool show_skin: UM.Preferences.getValue("layerview/show_skin")
            property bool show_infill: UM.Preferences.getValue("layerview/show_infill")

            anchors.top: UM.LayerView.compatibilityMode ? compatibilityModeLabel.bottom : layerTypeCombobox.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            CheckBox {
                checked: view_settings.extruder0_checked
                onClicked: {
                    UM.Preferences.setValue("layerview/extruder0_opacity", checked ? 1.0 : 0.0);
                }
                text: "Extruder 1"
                visible: !UM.LayerView.compatibilityMode && (UM.LayerView.extruderCount >= 1)
            }
            CheckBox {
                checked: view_settings.extruder1_checked
                onClicked: {
                    UM.Preferences.setValue("layerview/extruder1_opacity", checked ? 1.0 : 0.0);
                }
                text: "Extruder 2"
                visible: !UM.LayerView.compatibilityMode && (UM.LayerView.extruderCount >= 2)
            }
            CheckBox {
                checked: view_settings.extruder2_checked
                onClicked: {
                    UM.Preferences.setValue("layerview/extruder2_opacity", checked ? 1.0 : 0.0);
                }
                text: "Extruder 3"
                visible: !UM.LayerView.compatibilityMode && (UM.LayerView.etruderCount >= 3)
            }
            CheckBox {
                checked: view_settings.extruder3_checked
                onClicked: {
                    UM.Preferences.setValue("layerview/extruder3_opacity", checked ? 1.0 : 0.0);
                }
                text: "Extruder 4"
                visible: !UM.LayerView.compatibilityMode && (UM.LayerView.extruderCount >= 4)
            }
            Label {
                text: "Other extruders always visible"
                visible: !UM.LayerView.compatibilityMode && (UM.LayerView.extruderCount >= 5)
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
        }
    }
}
