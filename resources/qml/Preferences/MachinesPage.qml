// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

UM.ManagementPage
{
    id: base;

    title: catalog.i18nc("@title:tab", "Printers");
    model: UM.ContainerStacksModel
    {
        filter: {"type": "machine"}
    }

    activeId: Cura.MachineManager.activeMachineId
    activeIndex: activeMachineIndex()

    function activeMachineIndex()
    {
        for(var i = 0; i < model.rowCount(); i++) {
            if (model.getItem(i).id == Cura.MachineManager.activeMachineId) {
                return i;
            }
        }
        return -1;
    }

    buttons: [
        Button
        {
            text: catalog.i18nc("@action:button", "Activate");
            iconName: "list-activate";
            enabled: base.currentItem != null && base.currentItem.id != Cura.MachineManager.activeMaterialId
            onClicked: Cura.MachineManager.setActiveMachine(base.currentItem.id)
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Add");
            iconName: "list-add";
            onClicked: Printer.requestAddPrinter()
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Remove");
            iconName: "list-remove";
            enabled: base.currentItem != null && model.rowCount() > 1
            onClicked: confirmDialog.open();
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Rename");
            iconName: "edit-rename";
            enabled: base.currentItem != null
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
            font: UM.Theme.getFont("large")
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

                Button
                {
                    text: machineActionRepeater.model[index].label
                    onClicked:
                    {
                        actionDialog.content = machineActionRepeater.model[index].displayItem;
                        machineActionRepeater.model[index].displayItem.reset();
                        actionDialog.title = machineActionRepeater.model[index].label;
                        actionDialog.show();
                    }
                }
            }
        }

        UM.Dialog
        {
            id: actionDialog
            property var content
            onContentChanged:
            {
                contents = content;
                content.onCompleted.connect(hide)
                content.dialog = actionDialog
            }
            rightButtons: Button
            {
                text: catalog.i18nc("@action:button", "Close")
                iconName: "dialog-close"
                onClicked: actionDialog.reject()
            }
        }

        Row
        {
            anchors.top: machineActions.visible ? machineActions.bottom : machineActions.anchors.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.right: parent.right

            spacing: UM.Theme.getSize("default_margin").height

            Label
            {
                text: catalog.i18nc("@label", "Type")
                visible: base.currentItem && "definition_name" in base.currentItem.metadata
            }
            Label {
                text: (base.currentItem && "definition_name" in base.currentItem.metadata) ? base.currentItem.metadata.definition_name : ""
            }
        }

        UM.I18nCatalog { id: catalog; name: "uranium"; }

        UM.ConfirmRemoveDialog
        {
            id: confirmDialog;
            object: base.currentItem && base.currentItem.name ? base.currentItem.name : "";
            onYes:
            {
                Cura.MachineManager.removeMachine(base.currentItem.id);
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
            object: base.currentItem && base.currentItem.name ? base.currentItem.name : "";
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
