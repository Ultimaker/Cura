// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2

import UM 1.1 as UM

SettingItem
{
    id: base

    contents: Rectangle
    {
        id: control

        anchors.fill: parent

        border.width: UM.Theme.getSize("default_lining").width
        border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : hovered ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")

        color: {
            if (!enabled)
            {
                return UM.Theme.getColor("setting_control_disabled")
            }
            switch(propertyProvider.properties.validationState)
            {
                case "ValidatorState.Exception":
                    return UM.Theme.getColor("setting_validation_error")
                case "ValidatorState.MinimumError":
                    return UM.Theme.getColor("setting_validation_error")
                case "ValidatorState.MaximumError":
                    return UM.Theme.getColor("setting_validation_error")
                case "ValidatorState.MinimumWarning":
                    return UM.Theme.getColor("setting_validation_warning")
                case "ValidatorState.MaximumWarning":
                    return UM.Theme.getColor("setting_validation_warning")
                case "ValidatorState.Valid":
                    return UM.Theme.getColor("setting_validation_ok")

                default:
                    return UM.Theme.getColor("setting_control")
            }
        }

        Rectangle
        {
            anchors.fill: parent;
            anchors.margins: UM.Theme.getSize("default_lining").width;
            color: UM.Theme.getColor("setting_control_highlight")
            opacity: !control.hovered ? 0 : propertyProvider.properties.validationState == "ValidatorState.Valid" ? 1.0 : 0.35;
        }

        Label
        {
            anchors.right: parent.right;
            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
            anchors.verticalCenter: parent.verticalCenter;

            text: definition.unit;
            color: UM.Theme.getColor("setting_unit")
            font: UM.Theme.getFont("default")
        }

        MouseArea
        {
            id: mouseArea
            anchors.fill: parent;
            //hoverEnabled: true;
            cursorShape: Qt.IBeamCursor
        }

        TextInput
        {
            id: input

            anchors
            {
                left: parent.left
                leftMargin: UM.Theme.getSize("setting_unit_margin").width
                right: parent.right
                verticalCenter: parent.verticalCenter
            }

            Keys.onReleased:
            {
                propertyProvider.setPropertyValue("value", text)
            }

            onEditingFinished:
            {
                propertyProvider.setPropertyValue("value", text)
            }

            color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")
            font: UM.Theme.getFont("default");

            selectByMouse: true;

            maximumLength: 10;

            validator: RegExpValidator { regExp: (definition.type == "int") ? /^-?[0-9]{0,10}/ : /^-?[0-9.,]{0,10}/ } // definition.type property from parent loader used to disallow fractional number entry

            Binding
            {
                target: input
                property: "text"
                value:  {
                    if ((propertyProvider.properties.resolve != "None") && (stackLevel != 0) && (stackLevel != 1)) {
                        // We have a resolve function. Indicates that the setting is not settable per extruder and that
                        // we have to choose between the resolved value (default) and the global value
                        // (if user has explicitly set this).
                        return propertyProvider.properties.resolve;
                    } else {
                        return propertyProvider.properties.value;
                    }
                }
                when: !input.activeFocus
            }
        }
    }
}
