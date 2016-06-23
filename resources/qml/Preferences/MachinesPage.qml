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
    activeIndex: {
        for(var i = 0; i < model.rowCount(); i++) {
            if (model.getItem(i).id == Cura.MachineManager.activeMachineId) {
                return i;
            }
        }
        return -1;
    }

    onAddObject: Printer.requestAddPrinter()
    onRemoveObject: confirmDialog.open();
    onRenameObject: renameDialog.open();
    onActivateObject: Cura.MachineManager.setActiveMachine(base.currentItem.id)

    removeEnabled: base.currentItem != null && model.rowCount() > 1
    renameEnabled: base.currentItem != null
    activateEnabled: base.currentItem != null && base.currentItem.id != Cura.MachineManager.activeMachineId

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

        Row
        {
            id: machineActions
            anchors.left: parent.left
            anchors.top: machineName.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height

            Repeater
            {
                id: machineActionRepeater
                model: Cura.MachineActionManager.getSupportedActions(Cura.MachineManager.activeDefinitionId)

                Button
                {
                    text: machineActionRepeater.model[index].label;
                    onClicked:
                    {
                        actionDialog.content = machineActionRepeater.model[index].displayItem
                        machineActionRepeater.model[index].displayItem.reset()
                        actionDialog.show()
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
            }
        }

        Row
        {
            anchors.top: machineActions.visible ? machineActions.bottom : machineActions.anchors.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.left: parent.left
            anchors.right: parent.right

            spacing: UM.Theme.getSize("default_margin").height

            Label { text: catalog.i18nc("@label", "Type") }
            Label { text: base.currentItem ? base.currentItem.metadata.definition_name : "" }
        }

        UM.I18nCatalog { id: catalog; name: "uranium"; }

        UM.ConfirmRemoveDialog
        {
            id: confirmDialog;
            object: base.currentItem && base.currentItem.name ? base.currentItem.name : "";
            onYes: Cura.MachineManager.removeMachine(base.currentItem.id);
        }

        UM.RenameDialog
        {
            id: renameDialog;
            object: base.currentItem && base.currentItem.name ? base.currentItem.name : "";
            onAccepted:
            {
                Cura.MachineManager.renameMachine(base.currentItem.id, newName.trim());
                //Reselect current item to update details panel
                var index = objectList.currentIndex
                objectList.currentIndex = -1
                objectList.currentIndex = index
            }
        }
    }
}
