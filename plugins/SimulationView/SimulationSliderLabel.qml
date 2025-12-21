// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.5
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.1

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.PointingRectangle
{
    id: sliderLabelRoot

    property variant catalog: UM.I18nCatalog { name: "cura" }

    // custom properties
    property real maximumValue: 100
    property real value: 0
    property var setValue // Function
    property bool busy: false
    property int startFrom: 1
    property var layerData: ({})  // Dict with height, time_elapsed, layer_time, time_remaining

    target: Qt.point(parent.width, y + height / 2)
    arrowSize: UM.Theme.getSize("button_tooltip_arrow").height
    height: parent.height
    width: valueLabel.width
    visible: false

    color: UM.Theme.getColor("tool_panel_background")
    borderColor: UM.Theme.getColor("lining")
    borderWidth: UM.Theme.getSize("default_lining").width

    Behavior on height { NumberAnimation { duration: 50 } }

    // catch all mouse events so they're not handled by underlying 3D scene
    MouseArea
    {
        anchors.fill: parent
    }

    TextMetrics
    {
        id:     maxValueMetrics
        font:   valueLabel.font
        text:   maximumValue + 1 // layers are 0 based, add 1 for display value
    }

    TextField
    {
        id: valueLabel

        anchors.centerIn: parent

        //width: maxValueMetrics.contentWidth + 2 * UM.Theme.getSize("default_margin").width
        text: sliderLabelRoot.value + startFrom // the current handle value, add 1 because layers is an array
        horizontalAlignment: TextInput.AlignHCenter
        leftPadding: UM.Theme.getSize("narrow_margin").width
        rightPadding: UM.Theme.getSize("narrow_margin").width

        // key bindings, work when label is currently focused (active handle in LayerSlider)
        Keys.onUpPressed: sliderLabelRoot.setValue(sliderLabelRoot.value + ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))
        Keys.onDownPressed: sliderLabelRoot.setValue(sliderLabelRoot.value - ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))
        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("default")
        renderType: Text.NativeRendering
        background: Item {}
        selectByMouse: true

        onEditingFinished: {

            // Ensure that the cursor is at the first position. On some systems the text isn't fully visible
            // Seems to have to do something with different dpi densities that QML doesn't quite handle.
            // Another option would be to increase the size even further, but that gives pretty ugly results.
            cursorPosition = 0

            if (valueLabel.text != "") {
                // -startFrom because we need to convert back to an array structure
                sliderLabelRoot.setValue(parseInt(valueLabel.text) - startFrom)

            }
        }

        validator: IntValidator
        {
            bottom: startFrom
            top: sliderLabelRoot.maximumValue + startFrom // +startFrom because maybe we want to start in a different value rather than 0
        }

        Rectangle
        {
            id: layerHeightBackground
            x: -(width + UM.Theme.getSize("narrow_margin").width)
            y: (parent.height - height) / 2
            width: infoColumn.width + 2 * UM.Theme.getSize("default_margin").width
            height: infoColumn.height + 2 * UM.Theme.getSize("default_margin").height
            color: UM.Theme.getColor("tool_panel_background")
            radius: UM.Theme.getSize("default_radius").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width

            GridLayout
            {
                id: infoColumn
                anchors.centerIn: parent
                columns: 2
                columnSpacing: 1.5 * UM.Theme.getSize("default_margin").width
                rowSpacing: UM.Theme.getSize("narrow_margin").height

                // Current Height label
                Text
                {
                    text: catalog.i18nc("@label", "Current Height:")
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default")
                    renderType: Text.NativeRendering
                    Layout.alignment: Qt.AlignLeft
                }
                // Current Height value
                Text
                {
                    text: (sliderLabelRoot.layerData.height || 0).toFixed(2) + " mm"
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default_bold")
                    renderType: Text.NativeRendering
                    Layout.alignment: Qt.AlignRight
                    visible: sliderLabelRoot.layerData.height !== undefined
                }

                // Time Elapsed label
                Text
                {
                    text: catalog.i18nc("@label", "Time Elapsed:")
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default")
                    renderType: Text.NativeRendering
                    Layout.alignment: Qt.AlignLeft
                    visible: sliderLabelRoot.layerData.time_elapsed !== undefined
                }
                // Time Elapsed value
                Text
                {
                    text: sliderLabelRoot.layerData.time_elapsed || ""
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default_bold")
                    renderType: Text.NativeRendering
                    Layout.alignment: Qt.AlignRight
                    visible: sliderLabelRoot.layerData.time_elapsed !== undefined
                }

                // Layer Print Time label
                Text
                {
                    text: catalog.i18nc("@label", "Layer Print Time:")
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default")
                    renderType: Text.NativeRendering
                    Layout.alignment: Qt.AlignLeft
                    visible: sliderLabelRoot.layerData.layer_time !== undefined
                }
                // Layer Print Time value
                Text
                {
                    text: sliderLabelRoot.layerData.layer_time || ""
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default_bold")
                    renderType: Text.NativeRendering
                    Layout.alignment: Qt.AlignRight
                    visible: sliderLabelRoot.layerData.layer_time !== undefined
                }

                // Time Remaining label
                Text
                {
                    text: catalog.i18nc("@label", "Time Remaining:")
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default")
                    renderType: Text.NativeRendering
                    Layout.alignment: Qt.AlignLeft
                    visible: sliderLabelRoot.layerData.time_remaining !== undefined
                }
                // Time Remaining value
                Text
                {
                    text: sliderLabelRoot.layerData.time_remaining || ""
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default_bold")
                    renderType: Text.NativeRendering
                    Layout.alignment: Qt.AlignRight
                    visible: sliderLabelRoot.layerData.time_remaining !== undefined
                }
            }
        }
    }
    BusyIndicator
    {
        id: busyIndicator

        anchors
        {
            left: parent.right
            leftMargin: Math.round(UM.Theme.getSize("default_margin").width / 2)
            verticalCenter: parent.verticalCenter
        }

        width: sliderLabelRoot.height
        height: width

        visible: sliderLabelRoot.busy
        running: sliderLabelRoot.busy
    }
}
