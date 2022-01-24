// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.1 as UM
import Cura 1.0 as Cura

SettingItem
{
    id: base
    property var focusItem: control

    // Somehow if we directory set control.model to CuraApplication.getExtrudersModelWithOptional()
    // and in the Connections.onModelChanged use control.model as a reference, it will complain about
    // non-existing properties such as "onModelChanged" and "getItem". I guess if we access the model
    // via "control.model", it gives back a generic/abstract model instance. To avoid this, we add
    // this extra property to keep the ExtrudersModel and use this in the rest of the code.
    property var extrudersWithOptionalModel: CuraApplication.getExtrudersModelWithOptional()

    contents: ComboBox
    {
        id: control
        anchors.fill: parent

        model: base.extrudersWithOptionalModel

        Connections
        {
            target: base.extrudersWithOptionalModel
            function onModelChanged() { control.color = base.extrudersWithOptionalModel.getItem(control.currentIndex).color }
        }

        textRole: "name"

        onActivated:
        {
            if (model.getItem(index).enabled)
            {
                forceActiveFocus();
                propertyProvider.setPropertyValue("value", model.getItem(index).index);
            }
            else
            {
                if (propertyProvider.properties.value == -1)
                {
                    control.currentIndex = model.count - 1;  // we know the last item is "Not overridden"
                }
                else
                {
                    control.currentIndex = propertyProvider.properties.value;  // revert to the old value
                }
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

        property string color: "transparent"

        Binding
        {
            // We override the color property's value when the ExtruderModel changes. So we need to use an
            // explicit binding here otherwise we do not handle value changes after the model changes.
            target: control
            property: "color"
            value: control.currentText != "" ? control.model.getItem(control.currentIndex).color : "transparent"
        }

        indicator: UM.RecolorImage
        {
            id: downArrow
            x: control.width - width - control.rightPadding
            y: control.topPadding + Math.round((control.availableHeight - height) / 2)

            source: UM.Theme.getIcon("ChevronSingleDown")
            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height
            sourceSize.width: width + 5 * screenScaleFactor
            sourceSize.height: width + 5 * screenScaleFactor

            color: UM.Theme.getColor("setting_control_button");
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

        contentItem: Label
        {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
            anchors.right: downArrow.left
            rightPadding: swatch.width + UM.Theme.getSize("setting_unit_margin").width

            text: control.currentText
            textFormat: Text.PlainText
            renderType: Text.NativeRendering
            font: UM.Theme.getFont("default")
            color: enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")

            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter

            background: Rectangle
            {
                id: swatch
                height: Math.round(parent.height / 2)
                width: height
                radius: Math.round(width / 2)
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: UM.Theme.getSize("thin_margin").width

                color: control.color
            }
        }

        popup: Popup {
            y: control.height - UM.Theme.getSize("default_lining").height
            width: control.width
            implicitHeight: contentItem.implicitHeight + 2 * UM.Theme.getSize("default_lining").width
            padding: UM.Theme.getSize("default_lining").width

            contentItem: ListView {
                clip: true
                implicitHeight: contentHeight
                model: control.popup.visible ? control.delegateModel : null
                currentIndex: control.highlightedIndex

                ScrollIndicator.vertical: ScrollIndicator { }
            }

            background: Rectangle {
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
                anchors.fill: parent
                anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width

                text: model.name
                textFormat: Text.PlainText
                renderType: Text.NativeRendering
                color:
                {
                    if (model.enabled) {
                        UM.Theme.getColor("setting_control_text")
                    } else {
                        UM.Theme.getColor("action_button_disabled_text");
                    }
                }
                font: UM.Theme.getFont("default")
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
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
                border.color: parent.highlighted ? UM.Theme.getColor("setting_control_border_highlight") : "transparent"
            }
        }
    }
}
