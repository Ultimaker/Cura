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
    property var resetEnabled: false  // Keep PreferencesDialog happy

    UM.I18nCatalog { id: catalog; name: "cura"; }

    Cura.MaterialManagementModel {
        id: materialsModel
    }

    Label {
        id: titleLabel

        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
            margins: 5 * screenScaleFactor
        }

        font.pointSize: 18
        text: catalog.i18nc("@title:tab", "Materials")
    }

    property var hasCurrentItem: materialListView.currentItem != null

    property var currentItem:
    {  // is soon to be overwritten
        var current_index = materialListView.currentIndex;
        return materialsModel.getItem(current_index);
    }

    property var isCurrentItemActivated:
    {
        const extruder_position = Cura.ExtruderManager.activeExtruderIndex;
        const root_material_id = Cura.MachineManager.currentRootMaterialId[extruder_position];
        return base.currentItem.root_material_id == root_material_id;
    }

    Component.onCompleted:
    {
        // Select the activated material when this page shows up
        const extruder_position = Cura.ExtruderManager.activeExtruderIndex;
        const active_root_material_id = Cura.MachineManager.currentRootMaterialId[extruder_position];
        var itemIndex = -1;
        for (var i = 0; i < materialsModel.rowCount(); ++i)
        {
            var item = materialsModel.getItem(i);
            if (item.root_material_id == active_root_material_id)
            {
                itemIndex = i;
                break;
            }
        }
        materialListView.currentIndex = itemIndex;
    }

    Row  // Button Row
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

    property string newRootMaterialIdToSwitchTo: ""
    property bool toActivateNewMaterial: false

    // This connection makes sure that we will switch to the new
    Connections
    {
        target: materialsModel
        onItemsChanged: {
            var currentItemId = base.currentItem == null ? "" : base.currentItem.root_material_id;
            var position = Cura.ExtruderManager.activeExtruderIndex;

            // try to pick the currently selected item; it may have been moved
            if (base.newRootMaterialIdToSwitchTo == "") {
                base.newRootMaterialIdToSwitchTo = currentItemId;
            }

            for (var idx = 0; idx < materialsModel.rowCount(); ++idx) {
                var item = materialsModel.getItem(idx);
                if (item.root_material_id == base.newRootMaterialIdToSwitchTo) {
                    // Switch to the newly created profile if needed
                    materialListView.currentIndex = idx;
                    materialListView.activateDetailsWithIndex(materialListView.currentIndex);
                    if (base.toActivateNewMaterial) {
                        Cura.MachineManager.setMaterial(position, item.container_node);
                    }
                    base.newRootMaterialIdToSwitchTo = "";
                    base.toActivateNewMaterial = false;
                    return
                }
            }

            materialListView.currentIndex = 0;
            materialListView.activateDetailsWithIndex(materialListView.currentIndex);
            if (base.toActivateNewMaterial) {
                Cura.MachineManager.setMaterial(position, materialsModel.getItem(0).container_node);
            }
            base.newRootMaterialIdToSwitchTo = "";
            base.toActivateNewMaterial = false;
        }
    }

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
            if (result.status == "success") {
                messageDialog.icon = StandardIcon.Information;
                messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tag <filename>!", "Successfully imported material <filename>%1</filename>").arg(fileUrl);
            }
            else if (result.status == "duplicate") {
                messageDialog.icon = StandardIcon.Warning;
            }
            else {
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
            if (result.status == "error") {
                messageDialog.icon = StandardIcon.Critical;
                messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tags <filename> and <message>!", "Failed to export material to <filename>%1</filename>: <message>%2</message>").arg(fileUrl).arg(result.message);
                messageDialog.open();
            }
            else if (result.status == "success") {
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


    Item {
        id: contentsItem

        anchors {
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
        anchors {
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
            anchors {
                top: parent.top
                left: parent.left
            }
            visible: text != ""
            text: {
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
            anchors {
                top: captionLabel.visible ? captionLabel.bottom : parent.top
                topMargin: captionLabel.visible ? UM.Theme.getSize("default_margin").height : 0
                bottom: parent.bottom
                left: parent.left
            }

            Rectangle {
                parent: viewport
                anchors.fill: parent
                color: palette.light
            }

            width: true ? (parent.width * 0.4) | 0 : parent.width

            ListView
            {
                id: materialListView

                model: materialsModel

                section.property: "brand"
                section.criteria: ViewSection.FullString
                section.delegate: Rectangle
                {
                    width: materialScrollView.width
                    height: childrenRect.height
                    color: palette.light

                    Label
                    {
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_lining").width
                        text: section
                        font.bold: true
                        color: palette.text
                    }
                }

                delegate: Rectangle
                {
                    width: materialScrollView.width
                    height: childrenRect.height
                    color: ListView.isCurrentItem ? palette.highlight : (model.index % 2) ? palette.base : palette.alternateBase

                    Row
                    {
                        id: materialRow
                        spacing: (UM.Theme.getSize("default_margin").width / 2) | 0
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        anchors.right: parent.right

                        property bool isItemActivated:
                        {
                            const extruder_position = Cura.ExtruderManager.activeExtruderIndex;
                            const root_material_id = Cura.MachineManager.currentRootMaterialId[extruder_position];
                            return model.root_material_id == root_material_id;
                        }

                        Rectangle
                        {
                            width: Math.floor(parent.height * 0.8)
                            height: Math.floor(parent.height * 0.8)
                            color: model.color_code
                            border.color: parent.ListView.isCurrentItem ? palette.highlightedText : palette.text;
                            anchors.verticalCenter: parent.verticalCenter
                        }
                        Label
                        {
                            width: Math.floor((parent.width * 0.3))
                            text: model.material
                            elide: Text.ElideRight
                            font.italic: materialRow.isItemActivated
                            color: parent.ListView.isCurrentItem ? palette.highlightedText : palette.text;
                        }
                        Label
                        {
                            text: (model.name != model.material) ? model.name : ""
                            elide: Text.ElideRight
                            font.italic: materialRow.isItemActivated
                            color: parent.ListView.isCurrentItem ? palette.highlightedText : palette.text;
                        }
                    }

                    MouseArea
                    {
                        anchors.fill: parent
                        onClicked: {
                            parent.ListView.view.currentIndex = model.index;
                        }
                    }
                }

                function activateDetailsWithIndex(index) {
                    var model = materialsModel.getItem(index);
                    base.currentItem = model;
                    materialDetailsView.containerId = model.container_id;
                    materialDetailsView.currentMaterialNode = model.container_node;

                    detailsPanel.updateMaterialPropertiesObject();
                }

                onCurrentIndexChanged:
                {
                    forceActiveFocus();  // causes the changed fields to be saved
                    activateDetailsWithIndex(currentIndex);
                }
            }
        }


        Item
        {
            id: detailsPanel

            anchors {
                left: materialScrollView.right
                leftMargin: UM.Theme.getSize("default_margin").width
                top: parent.top
                bottom: parent.bottom
                right: parent.right
            }

            function updateMaterialPropertiesObject()
            {
                var currentItem = materialsModel.getItem(materialListView.currentIndex);

                materialProperties.name = currentItem.name;
                materialProperties.guid = currentItem.guid;

                materialProperties.brand = currentItem.brand ? currentItem.brand : "Unknown";
                materialProperties.material = currentItem.material ? currentItem.material : "Unknown";
                materialProperties.color_name = currentItem.color_name ? currentItem.color_name : "Yellow";
                materialProperties.color_code = currentItem.color_code ? currentItem.color_code : "yellow";

                materialProperties.description = currentItem.description ? currentItem.description : "";
                materialProperties.adhesion_info = currentItem.adhesion_info ? currentItem.adhesion_info : "";

                materialProperties.density = currentItem.density ? currentItem.density : 0.0;
                materialProperties.diameter = currentItem.diameter ? currentItem.diameter : 0.0;
                materialProperties.approximate_diameter = currentItem.approximate_diameter ? currentItem.approximate_diameter : "0";
            }

            Item
            {
                anchors.fill: parent

                Item    // Material title Label
                {
                    id: profileName

                    width: parent.width
                    height: childrenRect.height

                    Label {
                        text: materialProperties.name
                        font: UM.Theme.getFont("large")
                    }
                }

                MaterialView    // Material detailed information view below the title Label
                {
                    id: materialDetailsView
                    anchors
                    {
                        left: parent.left
                        right: parent.right
                        top: profileName.bottom
                        topMargin: UM.Theme.getSize("default_margin").height
                        bottom: parent.bottom
                    }

                    editingEnabled: base.currentItem != null && !base.currentItem.is_read_only

                    properties: materialProperties
                    containerId: base.currentItem != null ? base.currentItem.container_id : ""
                    currentMaterialNode: base.currentItem.container_node

                    property alias pane: base
                }

                QtObject
                {
                    id: materialProperties

                    property string guid: "00000000-0000-0000-0000-000000000000"
                    property string name: "Unknown";
                    property string profile_type: "Unknown";
                    property string brand: "Unknown";
                    property string material: "Unknown";  // This needs to be named as "material" to be consistent with
                                                          // the material container's metadata entry

                    property string color_name: "Yellow";
                    property color color_code: "yellow";

                    property real density: 0.0;
                    property real diameter: 0.0;
                    property string approximate_diameter: "0";

                    property real spool_cost: 0.0;
                    property real spool_weight: 0.0;
                    property real spool_length: 0.0;
                    property real cost_per_meter: 0.0;

                    property string description: "";
                    property string adhesion_info: "";
                }
            }
        }
    }
}
