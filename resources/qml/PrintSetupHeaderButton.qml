// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

// Button with a label-like appearance that displays different states (these can be displayed by setting the
// `valueError` or `valueWarning` properties). Mainly used within the `CustomConfiguration` component.

import QtQuick 2.1
import QtQuick.Controls 2.1

import Cura 1.0 as Cura
import UM 1.5 as UM

ToolButton
{
    id: base

    property alias tooltip: tooltip.text

    Cura.ToolTip
    {
        id: tooltip
        visible: base.hovered
        targetPoint: Qt.point(parent.x, Math.round(parent.y + parent.height / 2))
    }

    states:
    [
        State
        {
            name: "disabled"
            when: !base.enabled;
            PropertyChanges
            {
                target: background
                color: UM.Theme.getColor("setting_control_disabled")
                border.color: UM.Theme.getColor("setting_control_disabled_border")
            }
        },
        State
        {
            name: "value_error"
            when: base.enabled && base.valueError
            PropertyChanges
            {
                target: background
                color: UM.Theme.getColor("setting_validation_error_background")
                border.color: UM.Theme.getColor("setting_validation_error")
            }
        },
        State
        {
            name: "value_warning"
            when: base.enabled && base.valueWarning
            PropertyChanges
            {
                target: background
                color: UM.Theme.getColor("setting_validation_warning_background")
                border.color: UM.Theme.getColor("setting_validation_warning")
            }
        },
        State
        {
            name: "highlight"
            when: base.enabled && base.hovered
            PropertyChanges
            {
                target: background
                color: UM.Theme.getColor("setting_control")
                border.color: UM.Theme.getColor("setting_control_border_highlight")
            }
        },
        State
        {
            name: "neutral"
            when: base.enabled && !base.hovered && !base.valueWarning && !base.valueError
            PropertyChanges
            {
                target: background
                color: UM.Theme.getColor("setting_control")
                border.color: UM.Theme.getColor("setting_control_border")
            }
        }
    ]

    background: Rectangle
    {
        id: background

        radius: UM.Theme.getSize("setting_control_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        color: UM.Theme.getColor("setting_control")
        border.color: UM.Theme.getColor("setting_control_border")

        UM.RecolorImage
        {
            id: downArrow
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height
            sourceSize.height: width
            color: base.enabled ? UM.Theme.getColor("setting_control_button") : UM.Theme.getColor("setting_category_disabled_text")
            source: UM.Theme.getIcon("ChevronSingleDown")
        }
    }

    contentItem: UM.Label
    {
        id: printSetupComboBoxLabel
        text: base.text
        elide: Text.ElideRight;
        anchors.left: parent.left;
        anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
        anchors.right: downArrow.lef
        anchors.rightMargin: base.rightMargin
        anchors.verticalCenter: parent.verticalCenter
    }
}
