// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.1 as UM
import Cura 1.0 as Cura

SettingItem
{
    id: base
    property var focusItem: control

    contents: ComboBox
    {
        id: control
        anchors.fill: parent

        model: Cura.ExtrudersModel
        {
            onModelChanged: control.color = getItem(control.currentIndex).color
            addOptionalExtruder: true
        }

        textRole: "name"

        onActivated:
        {
            forceActiveFocus();
            propertyProvider.setPropertyValue("value", model.getItem(index).index);
        }

        onActiveFocusChanged:
        {
            if(activeFocus)
            {
                base.focusReceived();
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
                if(propertyProvider.properties.value == -1)
                {
                    return control.model.items.length - 1
                }
                return propertyProvider.properties.value
            }
            // Sometimes when the value is already changed, the model is still being built.
            // The when clause ensures that the current index is not updated when this happens.
            when: control.model.items.length > 0
        }

        MouseArea
        {
            anchors.fill: parent
            acceptedButtons: Qt.NoButton
            onWheel: wheel.accepted = true;
        }

        property string color: "#fff"

        Binding
        {
            // We override the color property's value when the ExtruderModel changes. So we need to use an
            // explicit binding here otherwise we do not handle value changes after the model changes.
            target: control
            property: "color"
            value: control.currentText != "" ? control.model.getItem(control.currentIndex).color : ""
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

            color: UM.Theme.getColor("setting_control_text");
        }

        background: Rectangle
        {
            color:
            {
                if (!enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled");
                }
                if (control.hovered || control.activeFocus)
                {
                    return UM.Theme.getColor("setting_control_highlight");
                }
                return UM.Theme.getColor("setting_control");
            }
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

        contentItem: Item
        {
            Label
            {
                id: extruderText

                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.right: swatch.left

                text: control.currentText
                font: UM.Theme.getFont("default")
                color: enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")

                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }

            Rectangle
            {
                id: swatch
                height: UM.Theme.getSize("setting_control").height / 2
                width: height

                anchors.right: parent.right
                anchors.rightMargin: downArrow.width + UM.Theme.getSize("setting_unit_margin").width
                anchors.verticalCenter: parent.verticalCenter
                anchors.margins: UM.Theme.getSize("default_margin").width / 4

                border.width: UM.Theme.getSize("default_lining").width
                border.color: enabled ? UM.Theme.getColor("setting_control_border") : UM.Theme.getColor("setting_control_disabled_border")
                radius: width / 2

                color: control.color
            }
        }

        delegate: ItemDelegate
        {
            width: control.width
            height: control.height
            highlighted: control.highlightedIndex == index

            contentItem: Text
            {
                text: model.name
                color: UM.Theme.getColor("setting_control_text")
                font: UM.Theme.getFont("default")
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}
