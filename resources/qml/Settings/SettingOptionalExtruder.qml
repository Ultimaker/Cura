// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

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

        style: ComboBoxStyle
        {
            background: Rectangle
            {
                color:
                {
                    if(!enabled)
                    {
                        return UM.Theme.getColor("setting_control_disabled");
                    }
                    if(control.hovered || control.activeFocus)
                    {
                        return UM.Theme.getColor("setting_control_highlight");
                    }
                    return UM.Theme.getColor("setting_control");
                }
                border.width: UM.Theme.getSize("default_lining").width
                border.color:
                {
                    if(!enabled)
                    {
                        return UM.Theme.getColor("setting_control_disabled_border")
                    }
                    if(control.hovered || control.activeFocus)
                    {
                        return UM.Theme.getColor("setting_control_border_highlight")
                    }
                    return UM.Theme.getColor("setting_control_border")
                }
            }
            label: Item
            {
                Label
                {
                    anchors.verticalCenter: parent.verticalCenter
                    width: parent.width - swatch.width - arrow.width;

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

                    anchors
                    {
                        right: arrow.left;
                        verticalCenter: parent.verticalCenter
                        margins: UM.Theme.getSize("default_margin").width / 4
                    }

                    border.width: UM.Theme.getSize("default_lining").width * 2
                    border.color: enabled ? UM.Theme.getColor("setting_control_border") : UM.Theme.getColor("setting_control_disabled_border")
                    radius: width / 2

                    color: control.color
                }
                UM.RecolorImage
                {
                    id: arrow
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter

                    source: UM.Theme.getIcon("arrow_bottom")
                    width: UM.Theme.getSize("standard_arrow").width
                    height: UM.Theme.getSize("standard_arrow").height
                    sourceSize.width: width + 5 * screenScaleFactor
                    sourceSize.height: width + 5 * screenScaleFactor

                    color: UM.Theme.getColor("setting_control_text")
                }
            }
        }
    }
}
