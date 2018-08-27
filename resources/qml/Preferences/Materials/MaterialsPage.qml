// Copyright (c) 2018 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: base

    property QtObject materialManager: CuraApplication.getMaterialManager()
    // Keep PreferencesDialog happy
    property var resetEnabled: false
    property var currentItem: null
    property var isCurrentItemActivated:
    {
        const extruder_position = Cura.ExtruderManager.activeExtruderIndex;
        const root_material_id = Cura.MachineManager.currentRootMaterialId[extruder_position];
        return base.currentItem.root_material_id == root_material_id;
    }
    property string newRootMaterialIdToSwitchTo: ""
    property bool toActivateNewMaterial: false

    // TODO: Save these to preferences
    property var collapsed_brands: []
    property var collapsed_types: []

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }
    Cura.MaterialBrandsModel { id: materialsModel }

    function findModelByRootId( search_root_id )
    {
        for (var i = 0; i < materialsModel.rowCount(); i++)
        {
            var types_model = materialsModel.getItem(i).material_types;
            for (var j = 0; j < types_model.rowCount(); j++)
            {
                var colors_model = types_model.getItem(j).colors;
                for (var k = 0; k < colors_model.rowCount(); k++)
                {
                    var material = colors_model.getItem(k);
                    if (material.root_material_id == search_root_id)
                    {
                        return material
                    }
                }
            }
        }
    }
    Component.onCompleted:
    {
        // Select the activated material when this page shows up
        const extruder_position = Cura.ExtruderManager.activeExtruderIndex;
        const active_root_material_id = Cura.MachineManager.currentRootMaterialId[extruder_position];
        console.log("goign to search for", active_root_material_id)
        base.currentItem = findModelByRootId(active_root_material_id)
    }

    onCurrentItemChanged: { MaterialsDetailsPanel.currentItem = currentItem }
    Connections
    {
        target: materialsModel
        onItemsChanged:
        {
            var currentItemId = base.currentItem == null ? "" : base.currentItem.root_material_id;
            var position = Cura.ExtruderManager.activeExtruderIndex;

            // try to pick the currently selected item; it may have been moved
            if (base.newRootMaterialIdToSwitchTo == "")
            {
                base.newRootMaterialIdToSwitchTo = currentItemId;
            }

            for (var idx = 0; idx < materialsModel.rowCount(); ++idx)
            {
                var item = materialsModel.getItem(idx);
                if (item.root_material_id == base.newRootMaterialIdToSwitchTo)
                {
                    // Switch to the newly created profile if needed
                    materialListView.currentIndex = idx;
                    materialListView.activateDetailsWithIndex(materialListView.currentIndex);
                    if (base.toActivateNewMaterial)
                    {
                        Cura.MachineManager.setMaterial(position, item.container_node);
                    }
                    base.newRootMaterialIdToSwitchTo = "";
                    base.toActivateNewMaterial = false;
                    return
                }
            }

            materialListView.currentIndex = 0;
            materialListView.activateDetailsWithIndex(materialListView.currentIndex);
            if (base.toActivateNewMaterial)
            {
                Cura.MachineManager.setMaterial(position, materialsModel.getItem(0).container_node);
            }
            base.newRootMaterialIdToSwitchTo = "";
            base.toActivateNewMaterial = false;
        }
    }

    // Main layout
    Label
    {
        id: titleLabel
        anchors
        {
            top: parent.top
            left: parent.left
            right: parent.right
            margins: 5 * screenScaleFactor
        }
        font.pointSize: 18
        text: catalog.i18nc("@title:tab", "Materials")
    }

    // Button Row
    Row
    {
        id: buttonRow
        anchors
        {
            left: parent.left
            right: parent.right
            top: titleLabel.bottom
        }
        height: childrenRect.height

        // Activate button
        Button
        {
            text: catalog.i18nc("@action:button", "Activate")
            iconName: "list-activate"
            enabled: !isCurrentItemActivated
            onClicked:
            {
                forceActiveFocus()

                const extruder_position = Cura.ExtruderManager.activeExtruderIndex;
                Cura.MachineManager.setMaterial(extruder_position, base.currentItem.container_node);
            }
        }

        // Create button
        Button
        {
            text: catalog.i18nc("@action:button", "Create")
            iconName: "list-add"
            onClicked:
            {
                forceActiveFocus();
                base.newRootMaterialIdToSwitchTo = base.materialManager.createMaterial();
                base.toActivateNewMaterial = true;
            }
        }

        // Duplicate button
        Button
        {
            text: catalog.i18nc("@action:button", "Duplicate");
            iconName: "list-add"
            enabled: base.hasCurrentItem
            onClicked:
            {
                forceActiveFocus();
                base.newRootMaterialIdToSwitchTo = base.materialManager.duplicateMaterial(base.currentItem.container_node);
                base.toActivateNewMaterial = true;
            }
        }

        // Remove button
        Button
        {
            text: catalog.i18nc("@action:button", "Remove")
            iconName: "list-remove"
            enabled: base.hasCurrentItem && !base.currentItem.is_read_only && !base.isCurrentItemActivated
            onClicked:
            {
                forceActiveFocus();
                confirmRemoveMaterialDialog.open();
            }
        }

        // Import button
        Button
        {
            text: catalog.i18nc("@action:button", "Import")
            iconName: "document-import"
            onClicked:
            {
                forceActiveFocus();
                importMaterialDialog.open();
            }
            visible: true
        }

        // Export button
        Button
        {
            text: catalog.i18nc("@action:button", "Export")
            iconName: "document-export"
            onClicked:
            {
                forceActiveFocus();
                exportMaterialDialog.open();
            }
            enabled: currentItem != null
        }
    }

    Item {
        id: contentsItem
        anchors
        {
            top: titleLabel.bottom
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            margins: 5 * screenScaleFactor
            bottomMargin: 0
        }
        clip: true
    }

    Item
    {
        anchors
        {
            top: buttonRow.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }

        SystemPalette { id: palette }

        Label
        {
            id: captionLabel
            anchors
            {
                top: parent.top
                left: parent.left
            }
            visible: text != ""
            text:
            {
                var caption = catalog.i18nc("@action:label", "Printer") + ": " + Cura.MachineManager.activeMachineName;
                if (Cura.MachineManager.hasVariants)
                {
                    caption += ", " + Cura.MachineManager.activeDefinitionVariantsName + ": " + Cura.MachineManager.activeVariantName;
                }
                return caption;
            }
            width: materialScrollView.width
            elide: Text.ElideRight
        }

        ScrollView
        {
            id: materialScrollView
            anchors
            {
                top: captionLabel.visible ? captionLabel.bottom : parent.top
                topMargin: captionLabel.visible ? UM.Theme.getSize("default_margin").height : 0
                bottom: parent.bottom
                left: parent.left
            }

            Rectangle
            {
                parent: viewport
                anchors.fill: parent
                color: palette.light
            }

            width: true ? (parent.width * 0.4) | 0 : parent.width
            frameVisible: true
            verticalScrollBarPolicy: Qt.ScrollBarAlwaysOn

            MaterialsList {}
        }

        MaterialsDetailsPanel
        {
            anchors
            {
                left: materialScrollView.right
                leftMargin: UM.Theme.getSize("default_margin").width
                top: parent.top
                bottom: parent.bottom
                right: parent.right
            }
        }
    }

    // Dialogs
    MessageDialog
    {
        id: confirmRemoveMaterialDialog
        icon: StandardIcon.Question;
        title: catalog.i18nc("@title:window", "Confirm Remove")
        text: catalog.i18nc("@label (%1 is object name)", "Are you sure you wish to remove %1? This cannot be undone!").arg(base.currentItem.name)
        standardButtons: StandardButton.Yes | StandardButton.No
        modality: Qt.ApplicationModal
        onYes:
        {
            base.materialManager.removeMaterial(base.currentItem.container_node);
        }
    }

    FileDialog
    {
        id: importMaterialDialog
        title: catalog.i18nc("@title:window", "Import Material")
        selectExisting: true
        nameFilters: Cura.ContainerManager.getContainerNameFilters("material")
        folder: CuraApplication.getDefaultPath("dialog_material_path")
        onAccepted:
        {
            var result = Cura.ContainerManager.importMaterialContainer(fileUrl);

            messageDialog.title = catalog.i18nc("@title:window", "Import Material");
            messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!", "Could not import material <filename>%1</filename>: <message>%2</message>").arg(fileUrl).arg(result.message);
            if (result.status == "success")
            {
                messageDialog.icon = StandardIcon.Information;
                messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tag <filename>!", "Successfully imported material <filename>%1</filename>").arg(fileUrl);
            }
            else if (result.status == "duplicate")
            {
                messageDialog.icon = StandardIcon.Warning;
            }
            else
            {
                messageDialog.icon = StandardIcon.Critical;
            }
            messageDialog.open();
            CuraApplication.setDefaultPath("dialog_material_path", folder);
        }
    }

    FileDialog
    {
        id: exportMaterialDialog
        title: catalog.i18nc("@title:window", "Export Material")
        selectExisting: false
        nameFilters: Cura.ContainerManager.getContainerNameFilters("material")
        folder: CuraApplication.getDefaultPath("dialog_material_path")
        onAccepted:
        {
            var result = Cura.ContainerManager.exportContainer(base.currentItem.root_material_id, selectedNameFilter, fileUrl);

            messageDialog.title = catalog.i18nc("@title:window", "Export Material");
            if (result.status == "error")
            {
                messageDialog.icon = StandardIcon.Critical;
                messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tags <filename> and <message>!", "Failed to export material to <filename>%1</filename>: <message>%2</message>").arg(fileUrl).arg(result.message);
                messageDialog.open();
            }
            else if (result.status == "success")
            {
                messageDialog.icon = StandardIcon.Information;
                messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tag <filename>!", "Successfully exported material to <filename>%1</filename>").arg(result.path);
                messageDialog.open();
            }
            CuraApplication.setDefaultPath("dialog_material_path", folder);
        }
    }

    MessageDialog
    {
        id: messageDialog
    }
}
