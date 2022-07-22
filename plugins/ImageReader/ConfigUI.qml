// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.3
import QtQuick.Window 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    title: catalog.i18nc("@title:window", "Convert Image")

    minimumWidth: grid.width + 2 * UM.Theme.getSize("default_margin").height
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight

    GridLayout
    {
        UM.I18nCatalog { id: catalog; name: "cura" }
        id: grid
        columnSpacing: UM.Theme.getSize("narrow_margin").width
        rowSpacing: UM.Theme.getSize("narrow_margin").height
        columns: 2

        UM.Label
        {
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            text: catalog.i18nc("@action:label", "Height (mm)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: peak_height_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        Cura.TextField
        {
            id: peak_height
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            selectByMouse: true
            objectName: "Peak_Height"
            validator: RegularExpressionValidator { regularExpression: /^\d{0,3}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onPeakHeightChanged(text)
        }

        UM.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The maximum distance of each pixel from \"Base.\"")
            visible: peak_height.hovered || peak_height_label.containsMouse
            targetPoint: Qt.point(peak_height.x + Math.round(peak_height.width / 2), 0)
            y: peak_height.y + peak_height.height + UM.Theme.getSize("default_margin").height
        }

        UM.Label
        {
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            text: catalog.i18nc("@action:label", "Base (mm)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea
            {
                id: base_height_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        Cura.TextField
        {
            id: base_height
            selectByMouse: true
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            objectName: "Base_Height"
            validator: RegularExpressionValidator { regularExpression: /^\d{0,3}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onBaseHeightChanged(text)
        }

        UM.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The base height from the build plate in millimeters.")
            visible: base_height.hovered || base_height_label.containsMouse
            targetPoint: Qt.point(base_height.x + Math.round(base_height.width / 2), 0)
            y: base_height.y + base_height.height + UM.Theme.getSize("default_margin").height
        }

        UM.Label
        {
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            text: catalog.i18nc("@action:label", "Width (mm)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: width_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        Cura.TextField
        {
            id: width
            selectByMouse: true
            objectName: "Width"
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            focus: true
            validator: RegularExpressionValidator { regularExpression: /^[1-9]\d{0,2}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onWidthChanged(text)
        }

        UM.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The width in millimeters on the build plate")
            visible: width.hovered || width_label.containsMouse
            targetPoint: Qt.point(width.x + Math.round(width.width / 2), 0)
            y: width.y + width.height + UM.Theme.getSize("default_margin").height
        }

        UM.Label
        {
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            text: catalog.i18nc("@action:label", "Depth (mm)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: depth_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        Cura.TextField
        {
            id: depth
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            selectByMouse: true
            objectName: "Depth"
            focus: true
            validator: RegularExpressionValidator { regularExpression: /^[1-9]\d{0,2}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onDepthChanged(text)
        }

        UM.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "The depth in millimeters on the build plate")
            visible: depth.hovered || depth_label.containsMouse
            targetPoint: Qt.point(depth.x + Math.round(depth.width / 2), 0)
            y: depth.y + depth.height + UM.Theme.getSize("default_margin").height
        }

        UM.Label
        {
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            text: ""
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: lighter_is_higher_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        Cura.ComboBox
        {
            id: lighter_is_higher
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            Layout.preferredHeight: UM.Theme.getSize("setting_control").height
            objectName: "Lighter_Is_Higher"
            textRole: "text"
            model: [
                { text: catalog.i18nc("@item:inlistbox", "Darker is higher") },
                { text: catalog.i18nc("@item:inlistbox", "Lighter is higher") }
            ]
            onCurrentIndexChanged: { manager.onImageColorInvertChanged(currentIndex) }
        }

        UM.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "For lithophanes dark pixels should correspond to thicker locations in order to block more light coming through. For height maps lighter pixels signify higher terrain, so lighter pixels should correspond to thicker locations in the generated 3D model.")
            visible: lighter_is_higher.hovered || lighter_is_higher_label.containsMouse
            targetPoint: Qt.point(lighter_is_higher.x + Math.round(lighter_is_higher.width / 2), 0)
            y: lighter_is_higher.y + lighter_is_higher.height + UM.Theme.getSize("default_margin").height
        }

        UM.Label
        {
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            text: catalog.i18nc("@action:label", "Color Model")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: color_model_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        Cura.ComboBox
        {
            id: color_model
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            Layout.preferredHeight: UM.Theme.getSize("setting_control").height
            objectName: "ColorModel"
            textRole: "text"
            model: [
                { text: catalog.i18nc("@item:inlistbox", "Linear") },
                { text: catalog.i18nc("@item:inlistbox", "Translucency") }
            ]
            onCurrentIndexChanged: { manager.onColorModelChanged(currentIndex) }
        }

        UM.ToolTip
        {
            text: catalog.i18nc("@info:tooltip", "For lithophanes a simple logarithmic model for translucency is available. For height maps the pixel values correspond to heights linearly.")
            visible: color_model.hovered || color_model_label.containsMouse
            targetPoint: Qt.point(color_model.x + Math.round(color_model.width / 2), 0)
            y: color_model.y + color_model.height + UM.Theme.getSize("default_margin").height
        }

        UM.Label
        {
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            text: catalog.i18nc("@action:label", "1mm Transmittance (%)")
            Layout.alignment: Qt.AlignVCenter

            MouseArea {
                id: transmittance_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        Cura.TextField
        {
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            selectByMouse: true
            objectName: "Transmittance"
            validator: RegularExpressionValidator { regularExpression: /^[1-9]\d{0,2}([\,|\.]\d*)?$/ }
            onTextChanged: manager.onTransmittanceChanged(text)

            UM.ToolTip
            {
                text: catalog.i18nc("@info:tooltip", "The percentage of light penetrating a print with a thickness of 1 millimeter. Lowering this value increases the contrast in dark regions and decreases the contrast in light regions of the image.")
                visible: parent.hovered || transmittance_label.containsMouse
                targetPoint: Qt.point(parent.x + Math.round(parent.width / 2), 0)
                y: parent.y + parent.height + UM.Theme.getSize("default_margin").height
            }
        }

        UM.Label
        {
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            text: catalog.i18nc("@action:label", "Smoothing")
            Layout.alignment: Qt.AlignVCenter

            MouseArea
            {
                id: smoothing_label
                anchors.fill: parent
                hoverEnabled: true
            }
        }

        Cura.SpinBox
        {
            id: smoothing
            Layout.fillWidth: true
            Layout.minimumWidth: UM.Theme.getSize("setting_control").width
            objectName: "Smoothing"
            to: 100.0
            stepSize: 1.0
            onValueChanged: manager.onSmoothingChanged(value)
        }

        UM.ToolTip
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

    buttonSpacing: UM.Theme.getSize("default_margin").width

    rightButtons: [
        Cura.TertiaryButton
        {
            id: cancel_button
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked: manager.onCancelButtonClicked()
        },
        Cura.PrimaryButton
        {
            id: ok_button
            text: catalog.i18nc("@action:button", "OK")
            onClicked: manager.onOkButtonClicked()
        }
    ]
}
