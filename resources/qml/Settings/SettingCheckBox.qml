// Copyright (c) 2018 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Layouts 1.2
import QtQuick.Controls 2.0

import UM 1.2 as UM

SettingItem
{
    id: base
    property var focusItem: control

    contents: MouseArea
    {
        id: control
        anchors
        {
            top: parent.top
            bottom: parent.bottom
            left: parent.left
        }
        width: UM.Theme.getSize("checkbox").width
        hoverEnabled: true

        property bool checked:
        {
            // FIXME this needs to go away once 'resolve' is combined with 'value' in our data model.
            // Stacklevels
            // 0: user  -> unsaved change
            // 1: quality changes  -> saved change
            // 2: quality
            // 3: material  -> user changed material in materials page
            // 4: variant
            // 5: machine
            var value
            if ((base.resolve !== undefined && base.resolve != "None") && (stackLevel != 0) && (stackLevel != 1))
            {
                // We have a resolve function. Indicates that the setting is not settable per extruder and that
                // we have to choose between the resolved value (default) and the global value
                // (if user has explicitly set this).
                value = base.resolve
            }
            else
            {
                value = propertyProvider.properties.value
            }

            switch(value)
            {
                case "True":
                    return true
                case "False":
                    return false
                default:
                    return (value !== undefined) ? value : false
            }
        }

        Keys.onSpacePressed:
        {
            forceActiveFocus()
            propertyProvider.setPropertyValue("value", !checked)
        }

        onClicked:
        {
            forceActiveFocus()
            propertyProvider.setPropertyValue("value", !checked)
        }

        Keys.onTabPressed:
        {
            base.setActiveFocusToNextSetting(true)
        }
        Keys.onBacktabPressed:
        {
            base.setActiveFocusToNextSetting(false)
        }

        onActiveFocusChanged:
        {
            if (activeFocus)
            {
                base.focusReceived()
            }
        }

        Rectangle
        {
            anchors
            {
                verticalCenter: parent.verticalCenter
                left: parent.left
            }
            width: UM.Theme.getSize("checkbox").width
            height: width

            radius: UM.Theme.getSize("checkbox_radius").width
            border.width: UM.Theme.getSize("default_lining").width

            border.color:
            {
                if(!enabled)
                {
                    return UM.Theme.getColor("checkbox_border_disabled")
                }
                switch (propertyProvider.properties.validationState)
                {
                    case "ValidatorState.Invalid":
                    case "ValidatorState.Exception":
                    case "ValidatorState.MinimumError":
                    case "ValidatorState.MaximumError":
                        return UM.Theme.getColor("setting_validation_error");
                    case "ValidatorState.MinimumWarning":
                    case "ValidatorState.MaximumWarning":
                        return UM.Theme.getColor("setting_validation_warning");
                }
                // Validation is OK.
                if (control.containsMouse || control.activeFocus || hovered)
                {
                    return UM.Theme.getColor("checkbox_border_hover")
                }
                return UM.Theme.getColor("checkbox_border")
            }

            color: {
                if (!enabled)
                {
                    return UM.Theme.getColor("checkbox_disabled")
                }
                switch (propertyProvider.properties.validationState)
                {
                    case "ValidatorState.Invalid":
                    case "ValidatorState.Exception":
                    case "ValidatorState.MinimumError":
                    case "ValidatorState.MaximumError":
                        return UM.Theme.getColor("setting_validation_error_background")
                    case "ValidatorState.MinimumWarning":
                    case "ValidatorState.MaximumWarning":
                        return UM.Theme.getColor("setting_validation_warning_background")
                }
                // Validation is OK.
                if (control.containsMouse || control.activeFocus)
                {
                    return UM.Theme.getColor("checkbox_hover")
                }
                return UM.Theme.getColor("checkbox")
            }

            UM.ColorImage
            {
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                height: UM.Theme.getSize("checkbox_mark").height
                width: UM.Theme.getSize("checkbox_mark").width
                color: !enabled ? UM.Theme.getColor("checkbox_mark_disabled") : UM.Theme.getColor("checkbox_mark");
                source: UM.Theme.getIcon("Check", "low")
                opacity: control.checked ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: 100; } }
            }
        }
    }
}
