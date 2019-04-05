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

    property int controlWidth: UM.Theme.getSize("setting_control").width
    property int controlHeight: UM.Theme.getSize("setting_control").height

    hoverEnabled: true
    selectByMouse: true
    font: UM.Theme.getFont("default")
    renderType: Text.NativeRendering

    background: Rectangle
    {
        anchors.fill: parent
        anchors.margins: Math.round(UM.Theme.getSize("default_lining").width)
        radius: UM.Theme.getSize("setting_control_radius").width

        border.color:
        {
            if (!textField.enabled)
            {
                return UM.Theme.getColor("setting_control_disabled_border")
            }
            if (!textField.acceptableInput)
            {
                return UM.Theme.getColor("setting_validation_error")
            }
            if (textField.hovered || textField.activeFocus)
            {
                return UM.Theme.getColor("setting_control_border_highlight")
            }
            return UM.Theme.getColor("setting_control_border")
        }

        color:
        {
            if (!textField.enabled)
            {
                return UM.Theme.getColor("setting_control_disabled")
            }
            if (!textField.acceptableInput)
            {
                return UM.Theme.getColor("setting_validation_error_background")
            }
            return UM.Theme.getColor("setting_control")
        }
    }
}
