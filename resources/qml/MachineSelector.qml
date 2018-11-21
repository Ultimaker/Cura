// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura
import "Menus"


Cura.ExpandableComponent
{
    id: machineSelector

    property bool isNetworkPrinter: Cura.MachineManager.activeMachineNetworkKey != ""

    popupPadding: 0
    popupAlignment: ExpandableComponent.PopupAlignment.AlignLeft
    iconSource: expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    headerItem: Label
    {
        text: isNetworkPrinter ? Cura.MachineManager.activeMachineNetworkGroupName : Cura.MachineManager.activeMachineName
        verticalAlignment: Text.AlignVCenter
        height: parent.height
        elide: Text.ElideRight
        renderType: Text.NativeRendering
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
    }

    popupItem: Item
    {
        id: popup
        width: UM.Theme.getSize("machine_selector_widget_content").width
        height: UM.Theme.getSize("machine_selector_widget_content").height

        ScrollView
        {
            id: scroll
            width: parent.width
            anchors.top: parent.top
            anchors.bottom: separator.top
            clip: true

            Column
            {
                id: column

                // Can't use parent.width since the parent is the flickable component and not the ScrollView
                width: scroll.width - 2 * UM.Theme.getSize("default_lining").width
                x: UM.Theme.getSize("default_lining").width

                Label
                {
                    text: catalog.i18nc("@label", "Network connected printers")
                    visible: networkedPrintersModel.items.length > 0
                    leftPadding: UM.Theme.getSize("default_margin").width
                    height: visible ? contentHeight + 2 * UM.Theme.getSize("default_margin").height : 0
                    renderType: Text.NativeRendering
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text_medium")
                    verticalAlignment: Text.AlignVCenter
                }

                Repeater
                {
                    id: networkedPrinters

                    model: UM.ContainerStacksModel
                    {
                        id: networkedPrintersModel
                        filter: {"type": "machine", "um_network_key": "*", "hidden": "False"}
                    }

                    delegate: Cura.ActionButton
                    {
                        text: model.metadata["connect_group_name"]
                        width: parent.width
                        height: UM.Theme.getSize("action_button").height
                        checked: Cura.MachineManager.activeMachineNetworkGroupName == model.metadata["connect_group_name"]
                        checkable: true

                        color: "transparent"
                        hoverColor: UM.Theme.getColor("action_button_hovered")
                        textColor: UM.Theme.getColor("text")
                        textHoverColor: UM.Theme.getColor("text")
                        outlineColor: checked ? UM.Theme.getColor("primary") : "transparent"

                        onClicked:
                        {
                            togglePopup()
                            Cura.MachineManager.setActiveMachine(model.id)
                        }

                        Connections
                        {
                            target: Cura.MachineManager
                            onActiveMachineNetworkGroupNameChanged: checked = Cura.MachineManager.activeMachineNetworkGroupName == model.metadata["connect_group_name"]
                        }
                    }
                }

                Label
                {
                    text: catalog.i18nc("@label", "Preset printers")
                    visible: virtualPrintersModel.items.length > 0
                    leftPadding: UM.Theme.getSize("default_margin").width
                    height: visible ? contentHeight + 2 * UM.Theme.getSize("default_margin").height : 0
                    renderType: Text.NativeRendering
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text_medium")
                    verticalAlignment: Text.AlignVCenter
                }

                Repeater
                {
                    id: virtualPrinters

                    model: UM.ContainerStacksModel
                    {
                        id: virtualPrintersModel
                        filter: {"type": "machine", "um_network_key": null}
                    }

                    delegate: Cura.ActionButton
                    {
                        text: model.name
                        width: parent.width
                        height: UM.Theme.getSize("action_button").height
                        checked: Cura.MachineManager.activeMachineId == model.id
                        checkable: true

                        color: "transparent"
                        hoverColor: UM.Theme.getColor("action_button_hovered")
                        textColor: UM.Theme.getColor("text")
                        textHoverColor: UM.Theme.getColor("text")
                        outlineColor: checked ? UM.Theme.getColor("primary") : "transparent"

                        onClicked:
                        {
                            togglePopup()
                            Cura.MachineManager.setActiveMachine(model.id)
                        }
                    }
                }
            }
        }

        Rectangle
        {
            id: separator

            anchors.bottom: buttonRow.top
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
            color: UM.Theme.getColor("lining")
        }

        Row
        {
            id: buttonRow

            anchors.bottom: parent.bottom
            anchors.horizontalCenter: parent.horizontalCenter
            padding: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("default_margin").width

            Cura.ActionButton
            {
                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width
                text: catalog.i18nc("@button", "Add printer")
                color: UM.Theme.getColor("secondary")
                hoverColor: UM.Theme.getColor("secondary")
                textColor: UM.Theme.getColor("primary")
                textHoverColor: UM.Theme.getColor("text")
                onClicked: Cura.Actions.addMachine.trigger()
            }

            Cura.ActionButton
            {
                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width
                text: catalog.i18nc("@button", "Manage printers")
                color: UM.Theme.getColor("secondary")
                hoverColor: UM.Theme.getColor("secondary")
                textColor: UM.Theme.getColor("primary")
                textHoverColor: UM.Theme.getColor("text")
                onClicked: Cura.Actions.configureMachines.trigger()
            }
        }
    }
}
