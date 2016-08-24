// Copyright (c) 2016 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

UM.ManagementPage
{
    id: base;

    title: catalog.i18nc("@title:tab", "Materials");

    model: UM.InstanceContainersModel
    {
        filter:
        {
            var result = { "type": "material" }
            if(Cura.MachineManager.filterMaterialsByMachine)
            {
                result.definition = Cura.MachineManager.activeDefinitionId
                if(Cura.MachineManager.hasVariants)
                {
                    result.variant = Cura.MachineManager.activeVariantId
                }
            }
            else
            {
                result.definition = "fdmprinter"
            }
            return result
        }

        sectionProperty: "brand"
    }

    activeId: Cura.MachineManager.activeMaterialId
    activeIndex: {
        for(var i = 0; i < model.rowCount(); i++) {
            if (model.getItem(i).id == Cura.MachineManager.activeMaterialId) {
                return i;
            }
        }
        return -1;
    }

    scrollviewCaption:
    {
        if (Cura.MachineManager.hasVariants)
        {
            catalog.i18nc("@action:label %1 is printer name, %2 is how this printer names variants, %3 is variant name", "Printer: %1, %2: %3").arg(Cura.MachineManager.activeMachineName).arg(Cura.MachineManager.activeDefinitionVariantsName).arg(Cura.MachineManager.activeVariantName)
        }
        else
        {
            catalog.i18nc("@action:label %1 is printer name","Printer: %1").arg(Cura.MachineManager.activeMachineName)
        }
    }
    detailsVisible: true

    section.property: "section"
    section.delegate: Label
    {
        text: section
        font.bold: true
        anchors.left: parent.left;
        anchors.leftMargin: UM.Theme.getSize("default_lining").width;
    }

    buttons: [
        Button
        {
            text: catalog.i18nc("@action:button", "Activate");
            iconName: "list-activate";
            enabled: base.currentItem != null && base.currentItem.id != Cura.MachineManager.activeMaterialId
            onClicked: Cura.MachineManager.setActiveMaterial(base.currentItem.id)
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Duplicate");
            iconName: "list-add";
            enabled: base.currentItem != null
            onClicked:
            {
                var material_id = Cura.ContainerManager.duplicateContainer(base.currentItem.id)
                if(material_id == "")
                {
                    return
                }

                if(Cura.MachineManager.filterQualityByMachine)
                {
                    var quality_id = Cura.ContainerManager.duplicateContainer(Cura.MachineManager.activeQualityId)
                    Cura.ContainerManager.setContainerMetaDataEntry(quality_id, "material", material_id)
                    Cura.MachineManager.setActiveQuality(quality_id)
                }

                Cura.MachineManager.setActiveMaterial(material_id)
            }
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Remove");
            iconName: "list-remove";
            enabled: base.currentItem != null && !base.currentItem.readOnly && !Cura.ContainerManager.isContainerUsed(base.currentItem.id)
            onClicked: confirmDialog.open()
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Import");
            iconName: "document-import";
            onClicked: importDialog.open();
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Export")
            iconName: "document-export"
            onClicked: exportDialog.open()
            enabled: currentItem != null
        }
    ]

    Item {
        UM.I18nCatalog { id: catalog; name: "cura"; }

        visible: base.currentItem != null
        anchors.fill: parent

        Item
        {
            id: profileName

            width: parent.width;
            height: childrenRect.height

            Label { text: materialProperties.name; font: UM.Theme.getFont("large"); }
            Button
            {
                id: editButton
                anchors.right: parent.right;
                text: catalog.i18nc("@action:button", "Edit");
                iconName: "document-edit";

                enabled: base.currentItem != null && !base.currentItem.readOnly

                checkable: enabled
            }
        }

        MaterialView
        {
            anchors
            {
                left: parent.left
                right: parent.right
                top: profileName.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                bottom: parent.bottom
            }

            editingEnabled: editButton.checkable && editButton.checked;

            properties: materialProperties
            containerId: base.currentItem != null ? base.currentItem.id : ""
        }

        QtObject
        {
            id: materialProperties

            property string name: "Unknown";
            property string profile_type: "Unknown";
            property string supplier: "Unknown";
            property string material_type: "Unknown";

            property string color_name: "Yellow";
            property color color_code: "yellow";

            property real density: 0.0;
            property real diameter: 0.0;

            property real spool_cost: 0.0;
            property real spool_weight: 0.0;
            property real spool_length: 0.0;
            property real cost_per_meter: 0.0;

            property string description: "";
            property string adhesion_info: "";
        }

        UM.ConfirmRemoveDialog
        {
            id: confirmDialog
            object: base.currentItem != null ? base.currentItem.name : ""
            onYes:
            {
                var containers = Cura.ContainerManager.findInstanceContainers({"id": base.currentItem.id})
                for(var i in containers)
                {
                    Cura.ContainerManager.removeContainer(containers[i])
                }
            }
        }

        FileDialog
        {
            id: importDialog;
            title: catalog.i18nc("@title:window", "Import Material");
            selectExisting: true;
            nameFilters: Cura.ContainerManager.getContainerNameFilters("material")
            folder: CuraApplication.getDefaultPath("dialog_material_path")
            onAccepted:
            {
                var result = Cura.ContainerManager.importContainer(fileUrl)

                messageDialog.title = catalog.i18nc("@title:window", "Import Material")
                messageDialog.text = catalog.i18nc("@info:status", "Could not import material <filename>%1</filename>: <message>%2</message>").arg(fileUrl).arg(result.message)
                if(result.status == "success")
                {
                    messageDialog.icon = StandardIcon.Information
                    messageDialog.text = catalog.i18nc("@info:status", "Successfully imported material <filename>%1</filename>").arg(fileUrl)
                }
                else if(result.status == "duplicate")
                {
                    messageDialog.icon = StandardIcon.Warning
                }
                else
                {
                    messageDialog.icon = StandardIcon.Critical
                }
                messageDialog.open()
                CuraApplication.setDefaultPath("dialog_material_path", folder)
            }
        }

        FileDialog
        {
            id: exportDialog;
            title: catalog.i18nc("@title:window", "Export Material");
            selectExisting: false;
            nameFilters: Cura.ContainerManager.getContainerNameFilters("material")
            folder: CuraApplication.getDefaultPath("dialog_material_path")
            onAccepted:
            {
                if(base.currentItem.metadata.base_file)
                {
                    var result = Cura.ContainerManager.exportContainer(base.currentItem.metadata.base_file, selectedNameFilter, fileUrl)
                }
                else
                {
                    var result = Cura.ContainerManager.exportContainer(base.currentItem.id, selectedNameFilter, fileUrl)
                }

                messageDialog.title = catalog.i18nc("@title:window", "Export Material")
                if(result.status == "error")
                {
                    messageDialog.icon = StandardIcon.Critical
                    messageDialog.text = catalog.i18nc("@info:status", "Failed to export material to <filename>%1</filename>: <message>%2</message>").arg(fileUrl).arg(result.message)
                    messageDialog.open()
                }
                else if(result.status == "success")
                {
                    messageDialog.icon = StandardIcon.Information
                    messageDialog.text = catalog.i18nc("@info:status", "Successfully exported material to <filename>%1</filename>").arg(result.path)
                    messageDialog.open()
                }
                CuraApplication.setDefaultPath("dialog_material_path", folder)
            }
        }

        MessageDialog
        {
            id: messageDialog
        }
    }

    onCurrentItemChanged:
    {
        if(currentItem == null)
        {
            return
        }
        materialProperties.name = currentItem.name;

        if(currentItem.metadata != undefined && currentItem.metadata != null)
        {
            materialProperties.supplier = currentItem.metadata.brand ? currentItem.metadata.brand : "Unknown";
            materialProperties.material_type = currentItem.metadata.material ? currentItem.metadata.material : "Unknown";
            materialProperties.color_name = currentItem.metadata.color_name ? currentItem.metadata.color_name : "Yellow";
            materialProperties.color_code = currentItem.metadata.color_code ? currentItem.metadata.color_code : "yellow";

            materialProperties.description = currentItem.metadata.description ? currentItem.metadata.description : "";
            materialProperties.adhesion_info = currentItem.metadata.adhesion_info ? currentItem.metadata.adhesion_info : "";

            if(currentItem.metadata.properties != undefined && currentItem.metadata.properties != null)
            {
                materialProperties.density = currentItem.metadata.properties.density ? currentItem.metadata.properties.density : 0.0;
                materialProperties.diameter = currentItem.metadata.properties.diameter ? currentItem.metadata.properties.diameter : 0.0;
            }
            else
            {
                materialProperties.density = 0.0;
                materialProperties.diameter = 0.0;
            }

        }
    }
}
