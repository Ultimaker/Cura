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
    property int numInstances: model.rowCount();
    model: UM.ContainerStacksModel
    {
        filter: {"type": "machine"}
        onDataChanged: numInstances = model.rowCount()
    }

    onAddObject: Printer.requestAddPrinter()
    onRemoveObject: confirmDialog.open();
    onRenameObject: renameDialog.open();

    removeEnabled: numInstances > 1
    renameEnabled: numInstances > 0

    Flow
    {
        anchors.fill: parent;
        spacing: UM.Theme.getSize("default_margin").height;

        Label
        {
            text: base.currentItem && base.currentItem.name ? base.currentItem.name : ""
            font: UM.Theme.getFont("large")
            width: parent.width
            elide: Text.ElideRight
        }

        Label { text: catalog.i18nc("@label", "Type"); width: parent.width * 0.2; }
        Label { text: base.currentItem && base.currentItem.typeName ? base.currentItem.typeName : ""; width: parent.width * 0.7; }

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
