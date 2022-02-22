// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Window 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura


UM.ManagementPage
{
    id: base

    title: catalog.i18nc("@title:tab", "Printers")
    model: Cura.GlobalStacksModel { }

    sectionRole: "discoverySource"

    activeId: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.id: ""
    activeIndex: activeMachineIndex()
    onHamburgeButtonClicked: menu.popup(content_item, content_item.width - menu.width, hamburger_button.height)

    function activeMachineIndex()
    {
        for(var i = 0; i < model.count; i++)
        {
            if (model.getItem(i).id == base.activeId)
            {
                return i;
            }
        }
        return -1;
    }

    buttons: [
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@action:button", "Add New")
            onClicked: Cura.Actions.addMachine.trigger()
        }
    ]

    Item
    {
        id: content_item
        visible: base.currentItem != null
        anchors.fill: parent


        UM.Label
        {
            id: machineName
            text: base.currentItem && base.currentItem.name ? base.currentItem.name : ""
            font: UM.Theme.getFont("large_bold")
            width: parent.width
            elide: Text.ElideRight
        }

        Flow
        {
            id: machineActions
            visible: currentItem && currentItem.id == Cura.MachineManager.activeMachine.id
            anchors
            {
                left: parent.left
                right: parent.right
                top: machineName.bottom
                topMargin: UM.Theme.getSize("default_margin").height
            }
            spacing: UM.Theme.getSize("default_margin").height

            Repeater
            {
                id: machineActionRepeater
                model: base.currentItem ? Cura.MachineActionManager.getSupportedActions(Cura.MachineManager.getDefinitionByMachineId(base.currentItem.id)) : null

                Item
                {
                    width: Math.round(childrenRect.width + 2 * screenScaleFactor)
                    height: childrenRect.height
                    Cura.SecondaryButton
                    {
                        text: machineActionRepeater.model[index].label
                        onClicked:
                        {
                            var currentItem = machineActionRepeater.model[index]
                            actionDialog.loader.manager = currentItem
                            actionDialog.loader.source = currentItem.qmlPath
                            actionDialog.title = currentItem.label
                            actionDialog.show()
                        }
                    }
                }
            }
        }

        UM.Dialog
        {
            id: actionDialog
            minimumWidth: UM.Theme.getSize("modal_window_minimum").width
            minimumHeight: UM.Theme.getSize("modal_window_minimum").height
            maximumWidth: minimumWidth * 3
            maximumHeight: minimumHeight * 3
        }

        UM.I18nCatalog { id: catalog; name: "cura"; }

        UM.ConfirmRemoveDialog
        {
            id: confirmDialog
            object: base.currentItem && base.currentItem.name ? base.currentItem.name : ""
            text: base.currentItem ? base.currentItem.removalWarning : ""

            onAccepted:
            {
                Cura.MachineManager.removeMachine(base.currentItem.id)
                if(!base.currentItem)
                {
                    objectList.currentIndex = activeMachineIndex()
                }
                //Force updating currentItem and the details panel
                objectList.onCurrentIndexChanged()
            }
        }

        UM.RenameDialog
        {
            id: renameDialog
            object: base.currentItem && base.currentItem.name ? base.currentItem.name : ""
            property var machine_name_validator: Cura.MachineNameValidator { }
            validName: renameDialog.newName.match(renameDialog.machine_name_validator.machineNameRegex) != null
            onAccepted:
            {
                Cura.MachineManager.renameMachine(base.currentItem.id, newName.trim())
                //Force updating currentItem and the details panel
                objectList.onCurrentIndexChanged()
            }
        }
        Cura.Menu
        {
            id: menu
            Cura.MenuItem
            {
                text: catalog.i18nc("@action:button", "Activate")
                enabled: base.currentItem != null && base.currentItem.id != Cura.MachineManager.activeMachine.id
                onTriggered: Cura.MachineManager.setActiveMachine(base.currentItem.id)
            }
            Cura.MenuItem
            {
                text: catalog.i18nc("@action:button", "Remove")
                enabled: base.currentItem != null && model.count > 1
                onTriggered: confirmDialog.open()
            }
            Cura.MenuItem
            {
                text: catalog.i18nc("@action:button", "Rename")
                enabled: base.currentItem != null && base.currentItem.metadata.group_name == null
                onTriggered:  renameDialog.open()
            }
       }

        Connections
        {
            target: Cura.MachineManager
            function onGlobalContainerChanged()
            {
                objectList.currentIndex = activeMachineIndex()
                objectList.onCurrentIndexChanged()
            }
        }
    }
}
