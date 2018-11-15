// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura
import "Menus"
import "Menus/ConfigurationMenu"

Cura.ExpandableComponent
{
    id: base

    property int currentModeIndex: -1
    property bool hideSettings: PrintInformation.preSliced

    property string enabledText: catalog.i18nc("@label:Should be short", "On")
    property string disabledText: catalog.i18nc("@label:Should be short", "Off")

    // This widget doesn't show tooltips by itself. Instead it emits signals so others can do something with it.
    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    implicitWidth: 200
    height: childrenRect.height
    iconSource: UM.Theme.getIcon("pencil")

    onCurrentModeIndexChanged: UM.Preferences.setValue("cura/active_mode", currentModeIndex)

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Timer
    {
        id: tooltipDelayTimer
        interval: 500
        repeat: false
        property var item
        property string text

        onTriggered: base.showTooltip(base, {x: 0, y: item.y}, text)
    }

    headerItem: RowLayout
    {
        anchors.fill: parent

        IconWithText
        {
            source: UM.Theme.getIcon("category_layer_height")
            text: Cura.MachineManager.activeQualityOrQualityChangesName + " " + layerHeight.properties.value + "mm"

            UM.SettingPropertyProvider
            {
                id: layerHeight
                containerStackId: Cura.MachineManager.activeStackId
                key: "layer_height"
                watchedProperties: ["value"]
            }
        }

        IconWithText
        {
            source: UM.Theme.getIcon("category_infill")
            text: parseInt(infillDensity.properties.value) + "%"

            UM.SettingPropertyProvider
            {
                id: infillDensity
                containerStackId: Cura.MachineManager.activeStackId
                key: "infill_sparse_density"
                watchedProperties: ["value"]
            }
        }

        IconWithText
        {
            source: UM.Theme.getIcon("category_support")
            text: supportEnabled.properties.value == "True" ? enabledText : disabledText


            UM.SettingPropertyProvider
            {
                id: supportEnabled
                containerStack: Cura.MachineManager.activeMachine
                key: "support_enable"
                watchedProperties: ["value"]
            }
        }

        IconWithText
        {
            source: UM.Theme.getIcon("category_adhesion")
            text: platformAdhesionType.properties.value != "skirt" && platformAdhesionType.properties.value != "none" ? enabledText : disabledText

            UM.SettingPropertyProvider
            {
                id: platformAdhesionType
                containerStack: Cura.MachineManager.activeMachine
                key: "adhesion_type"
                watchedProperties: [ "value"]
            }
        }
    }

    popupItem: Item
    {
        height: settingsModeSelection.height + sidebarContents.height + 2 * UM.Theme.getSize("default_margin").height
        width: UM.Theme.getSize("print_setup_widget").width
        ListView
        {
            // Settings mode selection toggle
            id: settingsModeSelection
            model: modesListModel
            height: UM.Theme.getSize("print_setup_mode_toggle").height
            visible: !hideSettings

            anchors
            {
                right: parent.right
                left: parent.left
                margins: UM.Theme.getSize("thick_margin").width
            }

            ButtonGroup
            {
                id: modeMenuGroup
            }

            delegate: Button
            {
                id: control

                height: settingsModeSelection.height
                width: Math.round(parent.width / 2)

                anchors.left: parent.left
                anchors.leftMargin: model.index * Math.round(settingsModeSelection.width / 2)
                anchors.verticalCenter: parent.verticalCenter

                ButtonGroup.group: modeMenuGroup

                checkable: true
                checked: base.currentModeIndex == index
                onClicked: base.currentModeIndex = index

                onHoveredChanged:
                {
                    if (hovered)
                    {
                        tooltipDelayTimer.item = settingsModeSelection
                        tooltipDelayTimer.text = model.tooltipText
                        tooltipDelayTimer.start()
                    }
                    else
                    {
                        tooltipDelayTimer.stop()
                        base.hideTooltip()
                    }
                }

                background: Rectangle
                {
                    border.width: control.checked ? UM.Theme.getSize("default_lining").width * 2 : UM.Theme.getSize("default_lining").width
                    border.color: (control.checked || control.pressed) ? UM.Theme.getColor("action_button_active_border") : control.hovered ? UM.Theme.getColor("action_button_hovered_border") : UM.Theme.getColor("action_button_border")

                    // For some reason, QtQuick decided to use the color of the background property as text color for the contentItem, so here it is
                    color: (control.checked || control.pressed) ? UM.Theme.getColor("action_button_active") : control.hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")
                }

                contentItem: Label
                {
                    text: model.text
                    font: UM.Theme.getFont("default")
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                    renderType: Text.NativeRendering
                    elide: Text.ElideRight
                    color:
                    {
                        if(control.pressed)
                        {
                            return UM.Theme.getColor("action_button_active_text")
                        }
                        else if(control.hovered)
                        {
                            return UM.Theme.getColor("action_button_hovered_text")
                        }
                        return UM.Theme.getColor("action_button_text")
                    }
                }
            }
        }

        Item
        {
            id: sidebarContents
            anchors.top: settingsModeSelection.bottom
            anchors.topMargin: UM.Theme.getSize("thick_margin").height
            anchors.left: parent.left
            anchors.right: parent.right
            height: UM.Theme.getSize("print_setup_widget").height

            visible: !hideSettings

            // We load both of them at once (instead of using a loader) because the advanced sidebar can take
            // quite some time to load. So in this case we sacrifice memory for speed.
            SidebarAdvanced
            {
                anchors.fill: parent
                visible: currentModeIndex == 1
                onShowTooltip: base.showTooltip(item, location, text)
                onHideTooltip: base.hideTooltip()
            }

            SidebarSimple
            {
                anchors.fill: parent
                visible: currentModeIndex != 1
                onShowTooltip: base.showTooltip(item, location, text)
                onHideTooltip: base.hideTooltip()
            }
        }

        // Setting mode: Recommended or Custom
        ListModel
        {
            id: modesListModel
        }

        Component.onCompleted:
        {
            modesListModel.append({
                text: catalog.i18nc("@title:tab", "Recommended"),
                tooltipText: "<b>%1</b><br/><br/>%2".arg(catalog.i18nc("@tooltip:title", "Recommended Print Setup")).arg(catalog.i18nc("@tooltip", "Print with the recommended settings for the selected printer, material and quality."))
            })
            modesListModel.append({
                text: catalog.i18nc("@title:tab", "Custom"),
                tooltipText: "<b>%1</b><br/><br/>%2".arg(catalog.i18nc("@tooltip:title", "Custom Print Setup")).arg(catalog.i18nc("@tooltip", "Print with finegrained control over every last bit of the slicing process."))
            })

            var index = Math.round(UM.Preferences.getValue("cura/active_mode"))

            if(index != null && !isNaN(index))
            {
                currentModeIndex = index
            }
            else
            {
                currentModeIndex = 0
            }
        }
    }
}
