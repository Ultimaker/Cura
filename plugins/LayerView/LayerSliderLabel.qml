// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.0 as UM
import Cura 1.0 as Cura

UM.PointingRectangle {
    id: sliderLabelRoot

    // custom properties
    property real maximumValue: 100
    property real value: 0
    property var setValue // Function
    property bool busy: false

    target: Qt.point(parent.width, y + height / 2)
    arrowSize: UM.Theme.getSize("default_arrow").width
    height: parent.height
    width: valueLabel.width + UM.Theme.getSize("default_margin").width

    color: UM.Theme.getColor("tool_panel_background")
    borderColor: UM.Theme.getColor("lining")
    borderWidth: UM.Theme.getSize("default_lining").width

    visible: true

    Behavior on height {
        NumberAnimation {
            duration: 50
        }
    }

    // catch all mouse events so they're not handled by underlying 3D scene
    MouseArea {
        anchors.fill: parent
    }

    TextField {
        id: valueLabel

        anchors {
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width / 2
            verticalCenter: parent.verticalCenter
        }

        // width is based on text field contents, but never smaller than 20pts
        width: 40 * screenScaleFactor

        text: sliderLabelRoot.value + 1 // the current handle value, add 1 because layers is an array
        horizontalAlignment: TextInput.AlignRight

        style: TextFieldStyle {
            textColor: UM.Theme.getColor("setting_control_text")
            font: UM.Theme.getFont("default")
            background: Item { }
        }

        onEditingFinished: {

            // Ensure that the cursor is at the first position. On some systems the text isn't fully visible
            // Seems to have to do something with different dpi densities that QML doesn't quite handle.
            // Another option would be to increase the size even further, but that gives pretty ugly results.
            cursorPosition = 0

            if (valueLabel.text != "") {
                // -1 because we need to convert back to an array structure
                sliderLabelRoot.setValue(parseInt(valueLabel.text) - 1)
            }
        }

        validator: IntValidator {
            bottom: 1
            top: sliderLabelRoot.maximumValue + 1 // +1 because actual layers is an array
        }

        Keys.onUpPressed: sliderLabelRoot.setValue(sliderLabelRoot.value + ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))
        Keys.onDownPressed: sliderLabelRoot.setValue(sliderLabelRoot.value - ((event.modifiers & Qt.ShiftModifier) ? 10 : 1))
    }

    BusyIndicator {
        id: busyIndicator

        anchors {
            left: parent.right
            leftMargin: UM.Theme.getSize("default_margin").width / 2
            verticalCenter: parent.verticalCenter
        }

        width: sliderLabelRoot.height
        height: width

        visible: sliderLabelRoot.busy
        running: sliderLabelRoot.busy
    }
}
