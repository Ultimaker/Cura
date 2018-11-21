// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
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
            anchors.fill: parent
            clip: true

            Column
            {
                id: column
                anchors.fill: parent

                Label
                {
                    text: catalog.i18nc("@label", "Network connected printers")
                    visible: networkedPrintersModel.items.length > 0
                    height: visible ? contentHeight + 2 * UM.Theme.getSize("default_margin").height : 0
                    renderType: Text.NativeRendering
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")
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

                    delegate: Button
                    {
                        text: name
                        width: parent.width
                        checkable: true
                        
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
                    height: visible ? contentHeight + 2 * UM.Theme.getSize("default_margin").height : 0
                    renderType: Text.NativeRendering
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")
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

                    delegate: Button
                    {
                        text: name
                        width: parent.width
                        checked: Cura.MachineManager.activeMachineId == model.id
                        checkable: true

                        onClicked:
                        {
                            togglePopup()
                            Cura.MachineManager.setActiveMachine(model.id)
                        }
                    }
                }
            }
        }
    }
}
