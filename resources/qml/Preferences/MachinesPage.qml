// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Window 2.1

import UM 1.2 as UM
import Cura 1.0 as Cura


UM.ManagementPage
{
    id: base;

    title: catalog.i18nc("@title:tab", "Printers");
    model: Cura.GlobalStacksModel { }

    sectionRole: "discoverySource"

    activeId: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.id: ""
    activeIndex: activeMachineIndex()

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
        Button
        {
            id: activateMenuButton
            text: catalog.i18nc("@action:button", "Activate");
            iconName: "list-activate";
            enabled: base.currentItem != null && base.currentItem.id != Cura.MachineManager.activeMaterialId
            onClicked: Cura.MachineManager.setActiveMachine(base.currentItem.id)
        },
        Button
        {
            id: addMenuButton
            text: catalog.i18nc("@action:button", "Add");
            iconName: "list-add";
            onClicked: Cura.Actions.addMachine.trigger()
        },
        Button
        {
            id: removeMenuButton
            text: catalog.i18nc("@action:button", "Remove");
            iconName: "list-remove";
            enabled: base.currentItem != null && model.count > 1
            onClicked: confirmDialog.open();
        },
        Button
        {
            id: renameMenuButton
            text: catalog.i18nc("@action:button", "Rename");
            iconName: "edit-rename";
            enabled: base.currentItem != null && base.currentItem.metadata.group_name == null
            onClicked: renameDialog.open();
        }
    ]

    Item
    {
        visible: base.currentItem != null
        anchors.fill: parent

        Label
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
            visible: currentItem && currentItem.id == Cura.MachineManager.activeMachineId
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: machineName.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height

            Repeater
            {
                id: machineActionRepeater
                model: base.currentItem ? Cura.MachineActionManager.getSupportedActions(Cura.MachineManager.getDefinitionByMachineId(base.currentItem.id)) : null

                Item
                {
                    width: Math.round(childrenRect.width + 2 * screenScaleFactor)
                    height: childrenRect.height
                    Button
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

            rightButtons: Button
            {
                text: catalog.i18nc("@action:button", "Close")
                iconName: "dialog-close"
                onClicked: actionDialog.reject()
            }
        }

        UM.I18nCatalog { id: catalog; name: "cura"; }

        UM.ConfirmRemoveDialog
        {
            id: confirmDialog
            object: base.currentItem && base.currentItem.name ? base.currentItem.name : ""
            onYes:
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
            id: renameDialog;
            width: 300 * screenScaleFactor
            height: 150 * screenScaleFactor
            object: base.currentItem && base.currentItem.name ? base.currentItem.name : "";
            property var machine_name_validator: Cura.MachineNameValidator { }
            validName: renameDialog.newName.match(renameDialog.machine_name_validator.machineNameRegex) != null;
            onAccepted:
            {
                Cura.MachineManager.renameMachine(base.currentItem.id, newName.trim());
                //Force updating currentItem and the details panel
                objectList.onCurrentIndexChanged()
            }
        }

        Connections
        {
            target: Cura.MachineManager
            onGlobalContainerChanged:
            {
                objectList.currentIndex = activeMachineIndex()
                objectList.onCurrentIndexChanged()
            }
        }

    }
}
