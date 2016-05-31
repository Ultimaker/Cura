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

        property alias hovered: mouseArea.containsMouse;

        border.width: UM.Theme.getSize("default_lining").width
        border.color: !enabled ? UM.Theme.getColor("setting_control_disabled_border") : hovered ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")

        property variant parentValue: value //From parent loader
        function notifyReset() {
            input.text = format(parentValue)
        }

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
            hoverEnabled: true;
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
//                 text = text.replace(",", ".") // User convenience. We use dots for decimal values
//                 if(parseFloat(text) != base.parentValue)
//                 {
//                     base.valueChanged(parseFloat(text));
//                 }

                propertyProvider.setPropertyValue("value", text)
            }

            onEditingFinished:
            {
//                 if(parseFloat(text) != base.parentValue)
//                 {
//                     base.valueChanged(parseFloat(text));
//                 }
                propertyProvider.setPropertyValue("value", text)
            }

            color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")
            font: UM.Theme.getFont("default");

            selectByMouse: true;

            maximumLength: 10;

            validator: RegExpValidator { regExp: /[0-9.,-]{0,10}/ }

            Binding
            {
                target: input
                property: "text"
                value: control.format(propertyProvider.properties.value)
                when: !input.activeFocus
            }
        }

        //Rounds a floating point number to 4 decimals. This prevents floating
        //point rounding errors.
        //
        //input:    The number to round.
        //decimals: The number of decimals (digits after the radix) to round to.
        //return:   The rounded number.
        function roundFloat(input, decimals)
        {
            //First convert to fixed-point notation to round the number to 4 decimals and not introduce new floating point errors.
            //Then convert to a string (is implicit). The fixed-point notation will be something like "3.200".
            //Then remove any trailing zeroes and the radix.
            return input.toFixed(decimals).replace(/\.?0*$/, ""); //Match on periods, if any ( \.? ), followed by any number of zeros ( 0* ), then the end of string ( $ ).
        }

        //Formats a value for display in the text field.
        //
        //This correctly handles formatting of float values.
        //
        //input:  The string value to format.
        //return: The formatted string.
        function format(inputValue) {
            return parseFloat(inputValue) ? roundFloat(parseFloat(inputValue), 4) : inputValue //If it's a float, round to four decimals.
        }
    }
}
