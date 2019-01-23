// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

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

        background: Rectangle
        {
            color:
            {
                if (!enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled")
                }

                if (control.hovered || control.activeFocus)
                {
                    return UM.Theme.getColor("setting_control_highlight")
                }

                return UM.Theme.getColor("setting_control")
            }

            radius: UM.Theme.getSize("setting_control_radius").width
            border.width: UM.Theme.getSize("default_lining").width
            border.color:
            {
                if (!enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled_border")
                }

                if (control.hovered || control.activeFocus)
                {
                    return UM.Theme.getColor("setting_control_border_highlight")
                }

                return UM.Theme.getColor("setting_control_border")
            }
        }

        indicator: UM.RecolorImage
        {
            id: downArrow
            x: control.width - width - control.rightPadding
            y: control.topPadding + Math.round((control.availableHeight - height) / 2)

            source: UM.Theme.getIcon("arrow_bottom")
            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height
            sourceSize.width: width + 5 * screenScaleFactor
            sourceSize.height: width + 5 * screenScaleFactor

            color: UM.Theme.getColor("setting_control_button")
        }

        contentItem: Label
        {
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: downArrow.left

            text: control.currentText
            textFormat: Text.PlainText
            renderType: Text.NativeRendering
            font: UM.Theme.getFont("default")
            color: !enabled ? UM.Theme.getColor("setting_control_disabled_text") : UM.Theme.getColor("setting_control_text")
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }

        popup: Popup
        {
            y: control.height - UM.Theme.getSize("default_lining").height
            width: control.width
            implicitHeight: contentItem.implicitHeight + 2 * UM.Theme.getSize("default_lining").width
            padding: UM.Theme.getSize("default_lining").width

            contentItem: ListView
            {
                clip: true
                implicitHeight: contentHeight
                model: control.popup.visible ? control.delegateModel : null
                currentIndex: control.highlightedIndex

                ScrollIndicator.vertical: ScrollIndicator { }
            }

            background: Rectangle
            {
                color: UM.Theme.getColor("setting_control")
                border.color: UM.Theme.getColor("setting_control_border")
            }
        }

        delegate: ItemDelegate
        {
            width: control.width - 2 * UM.Theme.getSize("default_lining").width
            height: control.height
            highlighted: control.highlightedIndex == index

            contentItem: Label
            {
                // FIXME: Somehow the top/bottom anchoring is not correct on Linux and it results in invisible texts.
                anchors.fill: parent
                anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width

                text: modelData.value
                textFormat: Text.PlainText
                renderType: Text.NativeRendering
                color: control.contentItem.color
                font: UM.Theme.getFont("default")
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }

            background: Rectangle
            {
                color: parent.highlighted ? UM.Theme.getColor("setting_control_highlight") : "transparent"
                border.color: parent.highlighted ? UM.Theme.getColor("setting_control_border_highlight") : "transparent"
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
                if ((base.resolve != "None") && (base.stackLevel != 0) && (base.stackLevel != 1))
                {
                    // We have a resolve function. Indicates that the setting is not settable per extruder and that
                    // we have to choose between the resolved value (default) and the global value
                    // (if user has explicitly set this).
                    value = base.resolve;
                }

                if (value == undefined)
                {
                    value = propertyProvider.properties.value;
                }

                for(var i = 0; i < control.model.length; ++i)
                {
                    if(control.model[i].key == value)
                    {
                        return i;
                    }
                }

                return -1;
            }
        }
    }
}
