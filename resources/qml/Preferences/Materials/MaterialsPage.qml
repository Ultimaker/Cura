// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.15
import QtQuick.Dialogs

import UM 1.5 as UM
import Cura 1.5 as Cura

UM.ManagementPage
{
    id: base
    Item { enabled: false; UM.I18nCatalog { id: catalog; name: "cura"} }
    // Keep PreferencesDialog happy
    property var resetEnabled: false
    property var currentItem: null

    property var materialManagementModel: CuraApplication.getMaterialManagementModel()

    property var hasCurrentItem: base.currentItem != null
    property var isCurrentItemActivated:
    {
        if (!hasCurrentItem)
        {
            return false
        }
        const extruder_position = Cura.ExtruderManager.activeExtruderIndex
        const root_material_id = Cura.MachineManager.currentRootMaterialId[extruder_position]
        return base.currentItem.root_material_id == root_material_id
    }
    property string newRootMaterialIdToSwitchTo: ""
    property bool toActivateNewMaterial: false

    property var extruder_position: Cura.ExtruderManager.activeExtruderIndex
    property var active_root_material_id: Cura.MachineManager.currentRootMaterialId[extruder_position]

    function resetExpandedActiveMaterial()
    {
        materialListView.expandActiveMaterial(active_root_material_id)
    }

    function setExpandedActiveMaterial(root_material_id)
    {
        materialListView.expandActiveMaterial(root_material_id)
    }

    // When loaded, try to select the active material in the tree
    Component.onCompleted:
    {
        resetExpandedActiveMaterial()
        base.newRootMaterialIdToSwitchTo = active_root_material_id
    }

    // Every time the selected item has changed, notify to the details panel
    onCurrentItemChanged:
    {
        forceActiveFocus()
        if(materialDetailsPanel.currentItem != currentItem)
        {
            materialDetailsPanel.currentItem = currentItem
            // CURA-6679 If the current item is gone after the model update, reset the current item to the active material.
            if (currentItem == null)
            {
                resetExpandedActiveMaterial()
            }
        }
    }

    title: catalog.i18nc("@title:tab", "Materials")
    detailsPlaneCaption: currentItem ? currentItem.name: ""
    scrollviewCaption: catalog.i18nc("@label", "Materials compatible with active printer:") + `<br /><b>${Cura.MachineManager.activeMachine.name}</b>`

    buttons: [
        Cura.SecondaryButton
        {
            id: createMenuButton
            text: catalog.i18nc("@action:button", "Create new")
            enabled: Cura.MachineManager.activeMachine.hasMaterials
            onClicked:
            {
                forceActiveFocus();
                base.newRootMaterialIdToSwitchTo = base.materialManagementModel.createMaterial();
                base.toActivateNewMaterial = true;
            }
        },
        Cura.SecondaryButton
        {
            id: importMenuButton
            text: catalog.i18nc("@action:button", "Import")
            onClicked:
            {
                forceActiveFocus();
                importMaterialDialog.open();
            }
            enabled: Cura.MachineManager.activeMachine.hasMaterials
        },
        Cura.SecondaryButton
        {
            id: syncMaterialsButton
            text: catalog.i18nc("@action:button", "Sync with Printers")
            onClicked:
            {
                forceActiveFocus();
                base.materialManagementModel.openSyncAllWindow();
            }
            visible: Cura.MachineManager.activeMachine.supportsMaterialExport
        }
    ]

    onHamburgeButtonClicked: {
        const hamburerButtonHeight = hamburger_button.height;
        menu.popup(hamburger_button, -menu.width + hamburger_button.width / 2, hamburger_button.height);
        // for some reason the height of the hamburger changes when opening the popup
        // reset height to initial heigt
        hamburger_button.height = hamburerButtonHeight;
    }
    listContent: ScrollView
    {
        id: materialScrollView
        anchors.fill: parent
        anchors.margins: parent.border.width
        width: (parent.width * 0.4) | 0

        clip: true
        ScrollBar.vertical: UM.ScrollBar
        {
            id: materialScrollBar
            parent: materialScrollView.parent
            anchors
            {
                top: parent.top
                right: parent.right
                bottom: parent.bottom
            }
        }
        contentHeight: materialListView.height //For some reason, this is not determined automatically with this ScrollView. Very weird!

        MaterialsList
        {
            id: materialListView
            width: materialScrollView.width - materialScrollBar.width
        }
    }

    MaterialsDetailsPanel
    {
        id: materialDetailsPanel
        anchors.fill: parent
    }

    Item
    {
        Cura.Menu
        {
            id: menu
            Cura.MenuItem
            {
                id: activateMenuButton
                text: catalog.i18nc("@action:button", "Activate")
                onClicked:
                {
                    forceActiveFocus()

                    // Set the current material as the one to be activated (needed to force the UI update)
                    base.newRootMaterialIdToSwitchTo = base.currentItem.root_material_id
                    const extruder_position = Cura.ExtruderManager.activeExtruderIndex
                    Cura.MachineManager.setMaterial(extruder_position, base.currentItem.container_node)
                }
            }
            Cura.MenuItem
            {
                id: duplicateMenuButton
                text: catalog.i18nc("@action:button", "Duplicate");
                enabled: base.hasCurrentItem
                onClicked:
                {
                    forceActiveFocus();
                    base.newRootMaterialIdToSwitchTo = base.materialManagementModel.duplicateMaterial(base.currentItem.container_node);
                    base.toActivateNewMaterial = true;
                }
            }
            Cura.MenuItem
            {
                id: removeMenuButton
                text: catalog.i18nc("@action:button", "Remove")
                enabled: base.hasCurrentItem && !base.currentItem.is_read_only && !base.isCurrentItemActivated && base.materialManagementModel.canMaterialBeRemoved(base.currentItem.container_node)

                onClicked:
                {
                    forceActiveFocus();
                    confirmRemoveMaterialDialog.open();
                }
            }
            Cura.MenuItem
            {
                id: exportMenuButton
                text: catalog.i18nc("@action:button", "Export")
                onClicked:
                {
                    forceActiveFocus();
                    exportMaterialDialog.open();
                }
                enabled: base.hasCurrentItem
            }
        }

        // Dialogs
        Cura.MessageDialog
        {
            id: confirmRemoveMaterialDialog
            title: catalog.i18nc("@title:window", "Confirm Remove")
            property string materialName: base.currentItem !== null ? base.currentItem.name : ""

            text: catalog.i18nc("@label (%1 is object name)", "Are you sure you wish to remove %1? This cannot be undone!").arg(materialName)
            standardButtons: Dialog.Yes | Dialog.No
            onAccepted:
            {
                // Set the active material as the fallback. It will be selected when the current material is deleted
                base.newRootMaterialIdToSwitchTo = base.active_root_material_id
                base.materialManagementModel.removeMaterial(base.currentItem.container_node);
            }
        }

        FileDialog
        {
            id: importMaterialDialog
            title: catalog.i18nc("@title:window", "Import Material")
            fileMode: FileDialog.OpenFile
            nameFilters: Cura.ContainerManager.getContainerNameFilters("material")
            currentFolder: CuraApplication.getDefaultPath("dialog_material_path")
            onAccepted:
            {
                const result = Cura.ContainerManager.importMaterialContainer(selectedFile);

                const messageDialog = Qt.createQmlObject("import Cura 1.5 as Cura; Cura.MessageDialog { onClosed: destroy() }", base);
                messageDialog.standardButtons = Dialog.Ok;
                messageDialog.title = catalog.i18nc("@title:window", "Import Material");
                switch (result.status)
                {
                    case "success":
                        messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tag <filename>!", "Successfully imported material <filename>%1</filename>").arg(selectedFile);
                        break;
                    default:
                        messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!", "Could not import material <filename>%1</filename>: <message>%2</message>").arg(selectedFile).arg(result.message);
                        break;
                }
                messageDialog.open();
                CuraApplication.setDefaultPath("dialog_material_path", currentFolder);
            }
        }

        FileDialog
        {
            id: exportMaterialDialog
            title: catalog.i18nc("@title:window", "Export Material")
            fileMode: FileDialog.SaveFile
            nameFilters: Cura.ContainerManager.getContainerNameFilters("material")
            currentFolder: CuraApplication.getDefaultPath("dialog_material_path")
            onAccepted:
            {
                const nameFilterString = selectedNameFilter.index >= 0 ? nameFilters[selectedNameFilter.index] : nameFilters[0];

                const result = Cura.ContainerManager.exportContainer(base.currentItem.root_material_id, nameFilterString, selectedFile);

                const messageDialog = Qt.createQmlObject("import Cura 1.5 as Cura; Cura.MessageDialog { onClosed: destroy() }", base);
                messageDialog.title = catalog.i18nc("@title:window", "Export Material");
                messageDialog.standardButtons = Dialog.Ok;
                switch (result.status)
                {
                    case "error":
                        messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tags <filename> and <message>!", "Failed to export material to <filename>%1</filename>: <message>%2</message>").arg(selectedFile).arg(result.message);
                        break;
                    case "success":
                        messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tag <filename>!", "Successfully exported material to <filename>%1</filename>").arg(result.path);
                        break;
                }
                messageDialog.open();

                CuraApplication.setDefaultPath("dialog_material_path", currentFolder);
            }
        }
    }
}
