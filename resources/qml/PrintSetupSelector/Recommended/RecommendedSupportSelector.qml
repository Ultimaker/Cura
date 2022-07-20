// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.0 as Cura


//
//  Enable support
//
Item
{
    id: enableSupportRow
    height: UM.Theme.getSize("print_setup_big_item").height

    property real labelColumnWidth: Math.round(width / 3)

    Item
    {
        id: enableSupportContainer
        width: labelColumnWidth + enableSupportCheckBox.width

        anchors
        {
            left: parent.left
            top: parent.top
            bottom: parent.bottom
            rightMargin: UM.Theme.getSize("thick_margin").width
        }

        Cura.IconWithText
        {
            id: enableSupportRowTitle
            anchors.left: parent.left
            visible: enableSupportCheckBox.visible
            source: UM.Theme.getIcon("Support")
            text: catalog.i18nc("@label", "Support")
            font: UM.Theme.getFont("medium")
            width: labelColumnWidth
            iconSize: UM.Theme.getSize("medium_button_icon").width
            tooltipText: catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, such parts would collapse during printing.")
        }

        UM.CheckBox
        {
            id: enableSupportCheckBox
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: enableSupportRowTitle.right

            property alias _hovered: enableSupportMouseArea.containsMouse

            enabled: recommendedPrintSetup.settingsEnabled

            visible: supportEnabled.properties.enabled == "True"
            checked: supportEnabled.properties.value == "True"

            MouseArea
            {
                id: enableSupportMouseArea
                anchors.fill: parent
                hoverEnabled: true
                // propagateComposedEvents used on supportToolTipMouseArea does not work with Controls Components.
                // It only works with other MouseAreas, so this is required
                onClicked: supportEnabled.setPropertyValue("value", supportEnabled.properties.value != "True")
            }
        }

        MouseArea
        {
            id: supportToolTipMouseArea
            anchors.fill: parent
            propagateComposedEvents: true
            hoverEnabled: true
            onEntered: base.showTooltip(enableSupportContainer, Qt.point(-enableSupportContainer.x - UM.Theme.getSize("thick_margin").width, 0),
                    catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, such parts would collapse during printing."))
            onExited: base.hideTooltip()
        }
    }

    ComboBox
    {
        id: supportExtruderCombobox

        height: UM.Theme.getSize("print_setup_big_item").height
        anchors
        {
            left: enableSupportContainer.right
            right: parent.right
            leftMargin: UM.Theme.getSize("default_margin").width
            rightMargin: UM.Theme.getSize("thick_margin").width
            verticalCenter: parent.verticalCenter
        }

        enabled: recommendedPrintSetup.settingsEnabled
        visible: enableSupportCheckBox.visible && (supportEnabled.properties.value == "True") && (extrudersEnabledCount.properties.value > 1)
        textRole: "name"  // this solves that the combobox isn't populated in the first time Cura is started

        model: extruderModel

        // knowing the extruder position, try to find the item index in the model
        function getIndexByPosition(position)
        {
            var itemIndex = -1  // if position is not found, return -1
            for (var item_index in model.items)
            {
                var item = model.getItem(item_index)
                if (item.index == position)
                {
                    itemIndex = item_index
                    break
                }
            }
            return itemIndex
        }

        onActivated:
        {
            if (model.getItem(index).enabled)
            {
                forceActiveFocus();
                supportExtruderNr.setPropertyValue("value", model.getItem(index).index);
            } else
            {
                currentIndex = supportExtruderNr.properties.value;  // keep the old value
            }
        }

        currentIndex: (supportExtruderNr.properties.value !== undefined) ? supportExtruderNr.properties.value : 0

        property string color: "#fff"
        Connections
        {
            target: extruderModel
            function onModelChanged()
            {
                var maybeColor = supportExtruderCombobox.model.getItem(supportExtruderCombobox.currentIndex).color
                if (maybeColor)
                {
                    supportExtruderCombobox.color = maybeColor
                }
            }
        }
        onCurrentIndexChanged:
        {
            var maybeColor = supportExtruderCombobox.model.getItem(supportExtruderCombobox.currentIndex).color
            if(maybeColor)
            {
                supportExtruderCombobox.color = maybeColor
            }
        }

        Binding
        {
            target: supportExtruderCombobox
            property: "currentIndex"
            value: supportExtruderCombobox.getIndexByPosition(supportExtruderNr.properties.value)
            // Sometimes when the value is already changed, the model is still being built.
            // The when clause ensures that the current index is not updated when this happens.
            when: supportExtruderCombobox.model.count > 0
        }

        indicator: UM.ColorImage
        {
            id: downArrow
            x: supportExtruderCombobox.width - width - supportExtruderCombobox.rightPadding
            y: supportExtruderCombobox.topPadding + Math.round((supportExtruderCombobox.availableHeight - height) / 2)

            source: UM.Theme.getIcon("ChevronSingleDown")
            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height

            color: UM.Theme.getColor("setting_control_button")
        }

        background: Rectangle
        {
            color:
            {
                if (!enabled)
                {
                    return UM.Theme.getColor("setting_control_disabled")
                }
                if (supportExtruderCombobox.hovered || base.activeFocus)
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
                if (supportExtruderCombobox.hovered || supportExtruderCombobox.activeFocus)
                {
                    return UM.Theme.getColor("setting_control_border_highlight")
                }
                return UM.Theme.getColor("setting_control_border")
            }
        }

        contentItem: UM.Label
        {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
            anchors.right: downArrow.left
            rightPadding: swatch.width + UM.Theme.getSize("setting_unit_margin").width

            text: supportExtruderCombobox.currentText
            textFormat: Text.PlainText
            color: enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")

            elide: Text.ElideLeft


            background: Rectangle
            {
                id: swatch
                height: Math.round(parent.height / 2)
                width: height
                radius: Math.round(width / 2)
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.rightMargin: UM.Theme.getSize("thin_margin").width

                color: supportExtruderCombobox.color
            }
        }

        popup: Popup
        {
            y: supportExtruderCombobox.height - UM.Theme.getSize("default_lining").height
            width: supportExtruderCombobox.width
            implicitHeight: contentItem.implicitHeight + 2 * UM.Theme.getSize("default_lining").width
            padding: UM.Theme.getSize("default_lining").width

            contentItem: ListView
            {
                implicitHeight: contentHeight

                ScrollBar.vertical: UM.ScrollBar {}
                clip: true
                model: supportExtruderCombobox.popup.visible ? supportExtruderCombobox.delegateModel : null
                currentIndex: supportExtruderCombobox.highlightedIndex
            }

            background: Rectangle
            {
                color: UM.Theme.getColor("setting_control")
                border.color: UM.Theme.getColor("setting_control_border")
            }
        }

        delegate: ItemDelegate
        {
            width: supportExtruderCombobox.width - 2 * UM.Theme.getSize("default_lining").width
            height: supportExtruderCombobox.height
            highlighted: supportExtruderCombobox.highlightedIndex == index

            contentItem: UM.Label
            {
                anchors.fill: parent
                anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width

                text: model.name
                color: model.enabled ? UM.Theme.getColor("setting_control_text"): UM.Theme.getColor("action_button_disabled_text")

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

                    color: supportExtruderCombobox.model.getItem(index).color
                }
            }

            background: Rectangle
            {
                color: parent.highlighted ? UM.Theme.getColor("setting_control_highlight") : "transparent"
                border.color: parent.highlighted ? UM.Theme.getColor("setting_control_border_highlight") : "transparent"
            }
        }
    }

    property var extruderModel: CuraApplication.getExtrudersModel()


    UM.SettingPropertyProvider
    {
        id: supportEnabled
        containerStack: Cura.MachineManager.activeMachine
        key: "support_enable"
        watchedProperties: [ "value", "enabled", "description" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: supportExtruderNr
        containerStack: Cura.MachineManager.activeMachine
        key: "support_extruder_nr"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineExtruderCount
        containerStack: Cura.MachineManager.activeMachine
        key: "machine_extruder_count"
        watchedProperties: ["value"]
        storeIndex: 0
    }
}
