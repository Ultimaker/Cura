// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Controls 2.3 as Controls2

import UM 1.2 as UM
import Cura 1.0 as Cura


//
//  Enable support
//
Item
{
    id: enableSupportRow
    height: childrenRect.height

    property real labelColumnWidth: Math.round(width / 3)

    Cura.IconWithText
    {
        id: enableSupportRowTitle
        anchors.top: parent.top
        anchors.left: parent.left
        visible: enableSupportCheckBox.visible
        source: UM.Theme.getIcon("category_support")
        text: catalog.i18nc("@label", "Support")
        font: UM.Theme.getFont("medium")
        width: labelColumnWidth
    }

    Item
    {
        id: enableSupportContainer
        height: enableSupportCheckBox.height

        anchors
        {
            left: enableSupportRowTitle.right
            right: parent.right
            verticalCenter: enableSupportRowTitle.verticalCenter
        }

        CheckBox
        {
            id: enableSupportCheckBox
            anchors.verticalCenter: parent.verticalCenter

            property alias _hovered: enableSupportMouseArea.containsMouse

            style: UM.Theme.styles.checkbox
            enabled: recommendedPrintSetup.settingsEnabled

            visible: supportEnabled.properties.enabled == "True"
            checked: supportEnabled.properties.value == "True"

            MouseArea
            {
                id: enableSupportMouseArea
                anchors.fill: parent
                hoverEnabled: true

                onClicked: supportEnabled.setPropertyValue("value", supportEnabled.properties.value != "True")

                onEntered:
                {
                    base.showTooltip(enableSupportCheckBox, Qt.point(-enableSupportContainer.x - UM.Theme.getSize("thick_margin").width, 0),
                        catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, such parts would collapse during printing."))
                }
                onExited: base.hideTooltip()
            }
        }

        Controls2.ComboBox
        {
            id: supportExtruderCombobox

            height: UM.Theme.getSize("print_setup_big_item").height
            anchors
            {
                left: enableSupportCheckBox.right
                right: parent.right
                leftMargin: UM.Theme.getSize("thick_margin").width
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

            indicator: UM.RecolorImage
            {
                id: downArrow
                x: supportExtruderCombobox.width - width - supportExtruderCombobox.rightPadding
                y: supportExtruderCombobox.topPadding + Math.round((supportExtruderCombobox.availableHeight - height) / 2)

                source: UM.Theme.getIcon("arrow_bottom")
                width: UM.Theme.getSize("standard_arrow").width
                height: UM.Theme.getSize("standard_arrow").height
                sourceSize.width: width + 5 * screenScaleFactor
                sourceSize.height: width + 5 * screenScaleFactor

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

            contentItem: Controls2.Label
            {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                anchors.right: downArrow.left
                rightPadding: swatch.width + UM.Theme.getSize("setting_unit_margin").width

                text: supportExtruderCombobox.currentText
                textFormat: Text.PlainText
                renderType: Text.NativeRendering
                font: UM.Theme.getFont("default")
                color: enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")

                elide: Text.ElideLeft
                verticalAlignment: Text.AlignVCenter

                background: UM.RecolorImage
                {
                    id: swatch
                    height: Math.round(parent.height / 2)
                    width: height
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.rightMargin: UM.Theme.getSize("thin_margin").width

                    sourceSize.width: width
                    sourceSize.height: height
                    source: UM.Theme.getIcon("extruder_button")
                    color: supportExtruderCombobox.color
                }
            }

            popup: Controls2.Popup
            {
                y: supportExtruderCombobox.height - UM.Theme.getSize("default_lining").height
                width: supportExtruderCombobox.width
                implicitHeight: contentItem.implicitHeight + 2 * UM.Theme.getSize("default_lining").width
                padding: UM.Theme.getSize("default_lining").width

                contentItem: ListView
                {
                    clip: true
                    implicitHeight: contentHeight
                    model: supportExtruderCombobox.popup.visible ? supportExtruderCombobox.delegateModel : null
                    currentIndex: supportExtruderCombobox.highlightedIndex

                    Controls2.ScrollIndicator.vertical: Controls2.ScrollIndicator { }
                }

                background: Rectangle
                {
                    color: UM.Theme.getColor("setting_control")
                    border.color: UM.Theme.getColor("setting_control_border")
                }
            }

            delegate: Controls2.ItemDelegate
            {
                width: supportExtruderCombobox.width - 2 * UM.Theme.getSize("default_lining").width
                height: supportExtruderCombobox.height
                highlighted: supportExtruderCombobox.highlightedIndex == index

                contentItem: Controls2.Label
                {
                    anchors.fill: parent
                    anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                    anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width

                    text: model.name
                    renderType: Text.NativeRendering
                    color:
                    {
                        if (model.enabled)
                        {
                            UM.Theme.getColor("setting_control_text")
                        }
                        else
                        {
                            UM.Theme.getColor("action_button_disabled_text");
                        }
                    }
                    font: UM.Theme.getFont("default")
                    elide: Text.ElideRight
                    verticalAlignment: Text.AlignVCenter
                    rightPadding: swatch.width + UM.Theme.getSize("setting_unit_margin").width

                    background: UM.RecolorImage
                    {
                        id: swatch
                        height: Math.round(parent.height / 2)
                        width: height
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.rightMargin: UM.Theme.getSize("thin_margin").width

                        sourceSize.width: width
                        sourceSize.height: height
                        source: UM.Theme.getIcon("extruder_button")
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