// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.8
import QtQuick.Controls 2.1

import UM 1.1 as UM

SettingItem
{
    id: base
    property var focusItem: control

    contents: ComboBox
    {
        id: control

        model: definition.options
        textRole: "value"

        anchors.fill: parent

        MouseArea
        {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            onWheel: wheel.accepted = true
        }

        background: Rectangle
        {
            color:
            {
                if (!enabled) {
                    return UM.Theme.getColor("setting_control_disabled")
                }

                if (control.hovered || control.activeFocus) {
                    return UM.Theme.getColor("setting_control_highlight")
                }

                return UM.Theme.getColor("setting_control")
            }

            border.width: UM.Theme.getSize("default_lining").width
            border.color:
            {
                if (!enabled) {
                    return UM.Theme.getColor("setting_control_disabled_border")
                }

                if (control.hovered || control.activeFocus) {
                    return UM.Theme.getColor("setting_control_border_highlight")
                }

                return UM.Theme.getColor("setting_control_border")
            }
        }

        indicator: UM.RecolorImage
        {
            id: downArrow
            x: control.width - width - control.rightPadding
            y: control.topPadding + (control.availableHeight - height) / 2

            source: UM.Theme.getIcon("arrow_bottom")
            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height
            sourceSize.width: width + 5 * screenScaleFactor
            sourceSize.height: width + 5 * screenScaleFactor

            color: UM.Theme.getColor("setting_control_text")
        }

        contentItem: Label
        {
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: downArrow.left

            text: control.currentText
            font: UM.Theme.getFont("default")
            color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }

        delegate: ItemDelegate
        {
            width: control.width
            height: control.height
            highlighted: control.highlightedIndex == index

            contentItem: Text
            {
                text: modelData.value
                color: control.contentItem.color
                font: UM.Theme.getFont("default")
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
        }

        onActivated:
        {
            forceActiveFocus()
            propertyProvider.setPropertyValue("value", definition.options[index].key)
        }

        onActiveFocusChanged:
        {
            if(activeFocus)
            {
                base.focusReceived()
            }
        }

        Keys.onTabPressed:
        {
            base.setActiveFocusToNextSetting(true)
        }

        Keys.onBacktabPressed:
        {
            base.setActiveFocusToNextSetting(false)
        }

        Binding
        {
            target: control
            property: "currentIndex"
            value:
            {
                // FIXME this needs to go away once 'resolve' is combined with 'value' in our data model.
                var value = undefined;
                if ((base.resolve != "None") && (base.stackLevel != 0) && (base.stackLevel != 1)) {
                    // We have a resolve function. Indicates that the setting is not settable per extruder and that
                    // we have to choose between the resolved value (default) and the global value
                    // (if user has explicitly set this).
                    value = base.resolve;
                }

                if (value == undefined) {
                    value = propertyProvider.properties.value;
                }

                for(var i = 0; i < control.model.length; ++i) {
                    if(control.model[i].key == value) {
                        return i;
                    }
                }

                return -1;
            }
        }
    }
}
