// Copyright (c) 2022 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.5 as UM
import Cura 1.5 as Cura

SettingItem
{
    id: base
    property var focusItem: control

    contents: Cura.ComboBox
    {
        id: control
        anchors.fill: parent

        forceHighlight: base.hovered

        property var extrudersModel: CuraApplication.getExtrudersModel()

        model: extrudersModel

        Connections
        {
            target: extrudersModel
            function onModelChanged()
            {
                control.color = extrudersModel.getItem(control.currentIndex).color
            }
        }

        textRole: "name"

        // knowing the extruder position, try to find the item index in the model
        function getIndexByPosition(position)
        {
            for (var item_index in model.items)
            {
                var item = model.getItem(item_index)
                if (item.index == position)
                {
                    return item_index
                }
            }
            return -1
        }

        onActivated:
        {
            if (model.getItem(index).enabled)
            {
                forceActiveFocus();
                propertyProvider.setPropertyValue("value", model.getItem(index).index);
            } else
            {
                currentIndex = propertyProvider.properties.value;  // keep the old value
            }
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

        currentIndex: propertyProvider.properties.value !== undefined ? propertyProvider.properties.value : 0

        property string color: "transparent"

        Binding
        {
            // We override the color property's value when the ExtruderModel changes. So we need to use an
            // explicit binding here otherwise we do not handle value changes after the model changes.
            target: control
            property: "color"
            value: control.currentText != "" ? control.model.getItem(control.currentIndex).color : "transparent"
        }

        Binding
        {
            target: control
            property: "currentIndex"
            value: control.getIndexByPosition(propertyProvider.properties.value)
            // Sometimes when the value is already changed, the model is still being built.
            // The when clause ensures that the current index is not updated when this happens.
            when: control.model.items.length > 0
        }

        indicator: UM.ColorImage
        {
            id: downArrow
            x: control.width - width - control.rightPadding
            y: control.topPadding + Math.round((control.availableHeight - height) / 2)

            source: UM.Theme.getIcon("ChevronSingleDown")
            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height

            color: UM.Theme.getColor("setting_control_button");
        }

        background: UM.UnderlineBackground
        {
            color:
            {
                if (!enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled")
                }
                if (control.hovered || base.activeFocus)
                {
                    return UM.Theme.getColor("setting_control_highlight")
                }
                return UM.Theme.getColor("setting_control")
            }
            borderColor: control.activeFocus ? UM.Theme.getSize("text_field_border_active") : "transparent"
            liningColor:
            {
                if(!enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled_border");
                }
                if(control.activeFocus)
                {
                    return UM.Theme.getColor("text_field_border_active");
                }
                if(base.hovered)
                {
                    return UM.Theme.getColor("text_field_border_hovered");
                }
                return UM.Theme.getColor("border_field_light");
            }
        }

        contentItem: UM.Label
        {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
            anchors.right: downArrow.left
            rightPadding: swatch.width + UM.Theme.getSize("setting_unit_margin").width

            text: control.currentText
            textFormat: Text.PlainText
            color: enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")

            background: Rectangle
            {
                id: swatch
                height: UM.Theme.getSize("standard_arrow").width
                width: height
                radius: Math.round(width / 2)
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: UM.Theme.getSize("thin_margin").width

                color: control.color
            }
        }

        popup: Popup
        {
            y: control.height - UM.Theme.getSize("default_lining").height
            width: control.width
            implicitHeight: contentItem.implicitHeight + 2 * UM.Theme.getSize("default_lining").width
            padding: UM.Theme.getSize("default_lining").width

            contentItem: ListView
            {
                implicitHeight: contentHeight

                ScrollBar.vertical: UM.ScrollBar {}
                clip: true
                model: control.popup.visible ? control.delegateModel : null
                currentIndex: control.highlightedIndex
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

            contentItem: UM.Label
            {
                anchors.fill: parent
                anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width

                text: model.name
                color: model.enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("action_button_disabled_text")
                elide: Text.ElideRight
                rightPadding: swatch.width + UM.Theme.getSize("setting_unit_margin").width

                background: Rectangle
                {
                    id: swatch
                    height: Math.round(parent.height / 2)
                    width: height
                    radius: Math.round(width / 2)
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.rightMargin: UM.Theme.getSize("thin_margin").width

                    color: control.model.getItem(index).color
                }
            }

            background: Rectangle
            {
                color: parent.highlighted ? UM.Theme.getColor("setting_control_highlight") : "transparent"
            }
        }
    }
}
