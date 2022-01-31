// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    title: catalog.i18nc("@title:window", "Convert Image...")

    minimumWidth: grid.width + 2 * UM.Theme.getSize("default_margin").height
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight

    GridLayout
    {
        UM.I18nCatalog { id: catalog; name: "cura" }
        id: grid
        columnSpacing: UM.Theme.getSize("default_margin").width
        rowSpacing: UM.Theme.getSize("thin_margin").height
        columns: 2

        Label
        {
            Layout.fillWidth: true
            text: catalog.i18nc("@action:label", "Height (mm)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: peak_height_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        TextField
        {
            id: peak_height
            Layout.fillWidth: true
            selectByMouse: true
            objectName: "Peak_Height"
            validator: RegExpValidator { regExp: /^\d{0,3}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onPeakHeightChanged(text)
        }

        Cura.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The maximum distance of each pixel from \"Base.\"")
            visible: peak_height.hovered || peak_height_label.containsMouse
            targetPoint: Qt.point(peak_height.x + Math.round(peak_height.width / 2), 0)
            y: peak_height.y + peak_height.height + UM.Theme.getSize("default_margin").height
        }

        Label
        {
            Layout.fillWidth: true
            text: catalog.i18nc("@action:label", "Base (mm)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: base_height_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        TextField
        {
            id: base_height
            selectByMouse: true
            Layout.fillWidth: true
            objectName: "Base_Height"
            validator: RegExpValidator { regExp: /^\d{0,3}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onBaseHeightChanged(text)
        }

        Cura.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The base height from the build plate in millimeters.")
            visible: base_height.hovered || base_height_label.containsMouse
            targetPoint: Qt.point(base_height.x + Math.round(base_height.width / 2), 0)
            y: base_height.y + base_height.height + UM.Theme.getSize("default_margin").height
        }

        Label
        {
            Layout.fillWidth: true
            text: catalog.i18nc("@action:label", "Width (mm)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: width_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        TextField
        {
            id: width
            selectByMouse: true
            objectName: "Width"
            Layout.fillWidth: true
            focus: true
            validator: RegExpValidator { regExp: /^[1-9]\d{0,2}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onWidthChanged(text)
        }

        Cura.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The width in millimeters on the build plate")
            visible: width.hovered || width_label.containsMouse
            targetPoint: Qt.point(width.x + Math.round(width.width / 2), 0)
            y: width.y + width.height + UM.Theme.getSize("default_margin").height
        }

        Label
        {
            Layout.fillWidth: true
            text: catalog.i18nc("@action:label", "Depth (mm)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: depth_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        TextField
        {
            id: depth
            Layout.fillWidth: true
            selectByMouse: true
            objectName: "Depth"
            focus: true
            validator: RegExpValidator { regExp: /^[1-9]\d{0,2}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onDepthChanged(text)
        }

        Cura.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The depth in millimeters on the build plate")
            visible: depth.hovered || depth_label.containsMouse
            targetPoint: Qt.point(depth.x + Math.round(depth.width / 2), 0)
            y: depth.y + depth.height + UM.Theme.getSize("default_margin").height
        }

        Label
        {
            Layout.fillWidth: true
            text: ""
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: lighter_is_higher_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        ComboBox
        {
            id: lighter_is_higher
            Layout.fillWidth: true
            Layout.preferredHeight: UM.Theme.getSize("toolbox_action_button").height
            objectName: "Lighter_Is_Higher"
            model: [catalog.i18nc("@item:inlistbox", "Darker is higher"), catalog.i18nc("@item:inlistbox", "Lighter is higher")]
            onCurrentIndexChanged: { manager.onImageColorInvertChanged(currentIndex) }
        }

        Cura.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "For lithophanes dark pixels should correspond to thicker locations in order to block more light coming through. For height maps lighter pixels signify higher terrain, so lighter pixels should correspond to thicker locations in the generated 3D model.")
            visible: lighter_is_higher.hovered || lighter_is_higher_label.containsMouse
            targetPoint: Qt.point(lighter_is_higher.x + Math.round(lighter_is_higher.width / 2), 0)
            y: lighter_is_higher.y + lighter_is_higher.height + UM.Theme.getSize("default_margin").height
        }

        Label
        {
            Layout.fillWidth: true
            text: catalog.i18nc("@action:label", "Color Model")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: color_model_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        ComboBox
        {
            id: color_model
            Layout.fillWidth: true
            objectName: "ColorModel"
            model: [catalog.i18nc("@item:inlistbox", "Linear"), catalog.i18nc("@item:inlistbox", "Translucency")]
            onCurrentIndexChanged: { manager.onColorModelChanged(currentIndex) }
            Layout.preferredHeight: UM.Theme.getSize("toolbox_action_button").height
        }

        Cura.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "For lithophanes a simple logarithmic model for translucency is available. For height maps the pixel values correspond to heights linearly.")
            visible: color_model.hovered || color_model_label.containsMouse
            targetPoint: Qt.point(color_model.x + Math.round(color_model.width / 2), 0)
            y: color_model.y + color_model.height + UM.Theme.getSize("default_margin").height
        }

        Label
        {
            Layout.fillWidth: true
            text: catalog.i18nc("@action:label", "1mm Transmittance (%)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: transmittance_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        TextField
        {
            id: transmittance
            Layout.fillWidth: true
            selectByMouse: true
            objectName: "Transmittance"
            validator: RegExpValidator { regExp: /^[1-9]\d{0,2}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onTransmittanceChanged(text)
        }

        Cura.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The percentage of light penetrating a print with a thickness of 1 millimeter. Lowering this value increases the contrast in dark regions and decreases the contrast in light regions of the image.")
            visible: transmittance.hovered || transmittance_label.containsMouse
            targetPoint: Qt.point(transmittance.x + Math.round(transmittance.width / 2), 0)
            y: transmittance.y + transmittance.height + UM.Theme.getSize("default_margin").height
        }

        Label
        {
            Layout.fillWidth: true
            text: catalog.i18nc("@action:label", "Smoothing")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: smoothing_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        Slider
        {
            id: smoothing
            Layout.fillWidth: true
            objectName: "Smoothing"
            to: 100.0
            stepSize: 1.0
            onValueChanged: { manager.onSmoothingChanged(value) }
        }

        Cura.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The amount of smoothing to apply to the image.")
            visible: smoothing.hovered || smoothing_label.containsMouse
            targetPoint: Qt.point(smoothing.x + Math.round(smoothing.width / 2), 0)
            y: smoothing.y + smoothing.height + UM.Theme.getSize("default_margin").height
        }
    }

    Item
    {
        ButtonGroup
        {
            buttons: [ok_button, cancel_button]
            checkedButton: ok_button
        }
    }

    onAccepted: manager.onOkButtonClicked()
    onRejected: manager.onCancelButtonClicked()

    rightButtons: [
        Button
        {
            id: ok_button
            text: catalog.i18nc("@action:button", "OK")
            onClicked: manager.onOkButtonClicked()
        },
        Button
        {
            id: cancel_button
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked: manager.onCancelButtonClicked()
        }
    ]
}
