// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.0 as Cura


RecommendedSettingSection
{
    id: enableSupportRow

    title: catalog.i18nc("@label", "Support")
    icon: UM.Theme.getIcon("Support")
    enableSectionVisible: supportEnabled.properties.enabled == "True"
    enableSectionChecked: supportEnabled.properties.value == "True"
    enableSectionEnabled: recommendedPrintSetup.settingsEnabled
    toolTipText: catalog.i18nc("@label", "Generate structures to support parts of the model which have overhangs. Without these structures, such parts would collapse during printing.")

    function onEnableSectionChanged(state) {
        supportEnabled.setPropertyValue("value", state)
    }

    property var extruderModel: CuraApplication.getExtrudersModel()


    property UM.SettingPropertyProvider supportEnabled: UM.SettingPropertyProvider
    {
        id: supportEnabled
        containerStack: Cura.MachineManager.activeMachine
        key: "support_enable"
        watchedProperties: [ "value", "enabled", "description" ]
        storeIndex: 0
    }

    property UM.SettingPropertyProvider supportExtruderNr: UM.SettingPropertyProvider
    {
        containerStack: Cura.MachineManager.activeMachine
        key: "support_extruder_nr"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    property UM.SettingPropertyProvider machineExtruderCount: UM.SettingPropertyProvider
    {
        containerStack: Cura.MachineManager.activeMachine
        key: "machine_extruder_count"
        watchedProperties: ["value"]
        storeIndex: 0
    }

    //Replace this with the Extruder selector
    contents: [
        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Print with")
            settingControl: Rectangle { color: "red"; width: 10; height:10 }
//            ComboBox
//        {
//            id: supportExtruderCombobox
//
//    //        height: UM.Theme.getSize("print_setup_big_item").height
//
//            enabled: recommendedPrintSetup.settingsEnabled
//            visible: (supportEnabled.properties.value == "True") && (extrudersEnabledCount.properties.value > 1)
//            textRole: "name"  // this solves that the combobox isn't populated in the first time Cura is started
//
//            model: extruderModel
//
//            // knowing the extruder position, try to find the item index in the model
//            function getIndexByPosition(position)
//            {
//                var itemIndex = -1  // if position is not found, return -1
//                for (var item_index in model.items)
//                {
//                    var item = model.getItem(item_index)
//                    if (item.index == position)
//                    {
//                        itemIndex = item_index
//                        break
//                    }
//                }
//                return itemIndex
//            }
//
//            onActivated:
//            {
//                if (model.getItem(index).enabled)
//                {
//                    forceActiveFocus();
//                    supportExtruderNr.setPropertyValue("value", model.getItem(index).index);
//                } else
//                {
//                    currentIndex = supportExtruderNr.properties.value;  // keep the old value
//                }
//            }
//
//    //        currentIndex: (supportExtruderNr.properties.value !== undefined) ? supportExtruderNr.properties.value : 0
//
//            property string color: "#fff"
//            Connections
//            {
//                target: extruderModel
//                function onModelChanged()
//                {
//                    var maybeColor = supportExtruderCombobox.model.getItem(supportExtruderCombobox.currentIndex).color
//                    if (maybeColor)
//                    {
//                        supportExtruderCombobox.color = maybeColor
//                    }
//                }
//            }
//            onCurrentIndexChanged:
//            {
//                var maybeColor = supportExtruderCombobox.model.getItem(supportExtruderCombobox.currentIndex).color
//                if(maybeColor)
//                {
//                    supportExtruderCombobox.color = maybeColor
//                }
//            }
//
//            Binding
//            {
//                target: supportExtruderCombobox
//                property: "currentIndex"
//                value: supportExtruderCombobox.getIndexByPosition(supportExtruderNr.properties.value)
//                // Sometimes when the value is already changed, the model is still being built.
//                // The when clause ensures that the current index is not updated when this happens.
//                when: supportExtruderCombobox.model.count > 0
//            }
//
//            indicator: UM.ColorImage
//            {
//                id: downArrow
//                x: supportExtruderCombobox.width - width - supportExtruderCombobox.rightPadding
//                y: supportExtruderCombobox.topPadding + Math.round((supportExtruderCombobox.availableHeight - height) / 2)
//
//                source: UM.Theme.getIcon("ChevronSingleDown")
//                width: UM.Theme.getSize("standard_arrow").width
//                height: UM.Theme.getSize("standard_arrow").height
//
//                color: UM.Theme.getColor("setting_control_button")
//            }
//
//            contentItem: UM.Label
//            {
//                anchors.verticalCenter: parent.verticalCenter
//                anchors.left: parent.left
//                anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
//                anchors.right: downArrow.left
//                rightPadding: swatch.width + UM.Theme.getSize("setting_unit_margin").width
//
//                text: supportExtruderCombobox.currentText
//                textFormat: Text.PlainText
//                color: enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
//
//                elide: Text.ElideLeft
//
//
//                background: Rectangle
//                {
//                    id: swatch
//                    height: Math.round(parent.height / 2)
//                    width: height
//                    radius: Math.round(width / 2)
//                    anchors.right: parent.right
//                    anchors.verticalCenter: parent.verticalCenter
//                    anchors.rightMargin: UM.Theme.getSize("thin_margin").width
//
//                    color: supportExtruderCombobox.color
//                }
//            }
//
//            popup: Popup
//            {
//                y: supportExtruderCombobox.height - UM.Theme.getSize("default_lining").height
//                width: supportExtruderCombobox.width
//                implicitHeight: contentItem.implicitHeight + 2 * UM.Theme.getSize("default_lining").width
//                padding: UM.Theme.getSize("default_lining").width
//
//                contentItem: ListView
//                {
//                    implicitHeight: contentHeight
//
//                    ScrollBar.vertical: UM.ScrollBar {}
//                    clip: true
//                    model: supportExtruderCombobox.popup.visible ? supportExtruderCombobox.delegateModel : null
//                    currentIndex: supportExtruderCombobox.highlightedIndex
//                }
//
//                background: Rectangle
//                {
//                    color: UM.Theme.getColor("setting_control")
//                    border.color: UM.Theme.getColor("setting_control_border")
//                }
//            }
//
//            delegate: ItemDelegate
//            {
//                width: supportExtruderCombobox.width - 2 * UM.Theme.getSize("default_lining").width
//                height: supportExtruderCombobox.height
//                highlighted: supportExtruderCombobox.highlightedIndex == index
//
//                contentItem: UM.Label
//                {
//                    anchors.fill: parent
//                    anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
//                    anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
//
//                    text: model.name
//                    color: model.enabled ? UM.Theme.getColor("setting_control_text"): UM.Theme.getColor("action_button_disabled_text")
//
//                    elide: Text.ElideRight
//                    rightPadding: swatch.width + UM.Theme.getSize("setting_unit_margin").width
//
//                    background: Rectangle
//                    {
//                        id: swatch
//                        height: Math.round(parent.height / 2)
//                        width: height
//                        radius: Math.round(width / 2)
//                        anchors.right: parent.right
//                        anchors.verticalCenter: parent.verticalCenter
//                        anchors.rightMargin: UM.Theme.getSize("thin_margin").width
//
//                        color: supportExtruderCombobox.model.getItem(index).color
//                    }
//                }
//
//                background: Rectangle
//                {
//                    color: parent.highlighted ? UM.Theme.getColor("setting_control_highlight") : "transparent"
//                    border.color: parent.highlighted ? UM.Theme.getColor("setting_control_border_highlight") : "transparent"
//                }
//            }
//        }
        },

        RecommendedSettingItem
        {
            settingName: catalog.i18nc("@action:label", "Placement")
            settingControl: Rectangle { color: "red"; width: 10; height:10 }
        }
    ]


}
