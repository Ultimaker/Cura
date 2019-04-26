// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// Cura-style TextField
//
TextField
{
    id: textField

    UM.I18nCatalog { id: catalog; name: "cura" }

    hoverEnabled: true
    selectByMouse: true
    font: UM.Theme.getFont("default")
    color: UM.Theme.getColor("text")
    renderType: Text.NativeRendering

    states: [
        State
        {
            name: "disabled"
            when: !textField.enabled
            PropertyChanges { target: backgroundRectangle.border; color: UM.Theme.getColor("setting_control_disabled_border")}
            PropertyChanges { target: backgroundRectangle; color: UM.Theme.getColor("setting_control_disabled")}
        },
        State
        {
            name: "invalid"
            when: !textField.acceptableInput
            PropertyChanges { target: backgroundRectangle.border; color: UM.Theme.getColor("setting_validation_error")}
            PropertyChanges { target: backgroundRectangle; color: UM.Theme.getColor("setting_validation_error_background")}
        },
        State
        {
            name: "hovered"
            when: textField.hovered || textField.activeFocus
            PropertyChanges { target: backgroundRectangle.border; color: UM.Theme.getColor("setting_control_border_highlight") }
        }
    ]

    background: Rectangle
    {
        id: backgroundRectangle

        color: UM.Theme.getColor("main_background")

        anchors.margins: Math.round(UM.Theme.getSize("default_lining").width)
        radius: UM.Theme.getSize("setting_control_radius").width

        border.color:
        {
            if (!textField.enabled)
            {
                return UM.Theme.getColor("setting_control_disabled_border")
            }
            if (textField.hovered || textField.activeFocus)
            {
                return UM.Theme.getColor("setting_control_border_highlight")
            }
            return UM.Theme.getColor("setting_control_border")
        }
    }
}
