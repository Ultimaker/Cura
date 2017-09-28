//Copyright (c) 2017 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

UM.ManagementPage
{
    id: base;

    title: catalog.i18nc("@title:tab", "Materials");

    Component.onCompleted:
    {
        // Workaround to make sure all of the items are visible
        objectList.positionViewAtBeginning();
    }

    model: Cura.MaterialsModel
    {
        filter:
        {
            var result = { "type": "material", "approximate_diameter": Math.round(materialDiameterProvider.properties.value).toString() }
            if(Cura.MachineManager.filterMaterialsByMachine)
            {
                result.definition = Cura.MachineManager.activeQualityDefinitionId;
                if(Cura.MachineManager.hasVariants)
                {
                    result.variant = Cura.MachineManager.activeQualityVariantId;
                }
            }
            else
            {
                result.definition = "fdmprinter";
                result.compatible = true; //NB: Only checks for compatibility in global version of material, but we don't have machine-specific materials anyway.
            }
            return result
        }

        sectionProperty: "brand"
    }

    delegate: Rectangle
    {
        width: objectList.width;
        height: childrenRect.height;
        color: isCurrentItem ? palette.highlight : index % 2 ? palette.base : palette.alternateBase
        property bool isCurrentItem: ListView.isCurrentItem

        Row
        {
            spacing: (UM.Theme.getSize("default_margin").width / 2) | 0
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            Rectangle
            {
                width: (parent.height * 0.8) | 0
                height: (parent.height * 0.8) | 0
                color: model.metadata.color_code
                border.color: isCurrentItem ? palette.highlightedText : palette.text;
                anchors.verticalCenter: parent.verticalCenter
            }
            Label
            {
                width: (parent.width * 0.3) | 0
                text: model.metadata.material
                elide: Text.ElideRight
                font.italic: model.id == activeId
                color: isCurrentItem ? palette.highlightedText : palette.text;
            }
            Label
            {
                text: (model.name != model.metadata.material) ? model.name : ""
                elide: Text.ElideRight
                font.italic: model.id == activeId
                color: isCurrentItem ? palette.highlightedText : palette.text;
            }
        }

        MouseArea
        {
            anchors.fill: parent;
            onClicked:
            {
                forceActiveFocus();
                if(!parent.ListView.isCurrentItem)
                {
                    parent.ListView.view.currentIndex = index;
                    base.itemActivated();
                }
            }
        }
    }

    activeId: Cura.MachineManager.activeMaterialId
    activeIndex: getIndexById(activeId)
    function getIndexById(material_id)
    {
        for(var i = 0; i < model.rowCount(); i++) {
            if (model.getItem(i).id == material_id) {
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
            enabled: base.currentItem != null && base.currentItem.id != Cura.MachineManager.activeMaterialId && Cura.MachineManager.hasMaterials
            onClicked:
            {
                forceActiveFocus();
                Cura.MachineManager.setActiveMaterial(base.currentItem.id)
                currentItem = base.model.getItem(base.objectList.currentIndex) // Refresh the current item.
            }
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Create")
            iconName: "list-add"
            onClicked:
            {
                forceActiveFocus();
                var material_id = Cura.ContainerManager.createMaterial()
                if(material_id == "")
                {
                    return
                }
                if(Cura.MachineManager.hasMaterials)
                {
                    Cura.MachineManager.setActiveMaterial(material_id)
                }
                base.objectList.currentIndex = base.getIndexById(material_id);
            }
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Duplicate");
            iconName: "list-add";
            enabled: base.currentItem != null
            onClicked:
            {
                forceActiveFocus();
                var base_file = Cura.ContainerManager.getContainerMetaDataEntry(base.currentItem.id, "base_file")
                // We need to copy the base container instead of the specific variant.
                var material_id = base_file == "" ? Cura.ContainerManager.duplicateMaterial(base.currentItem.id): Cura.ContainerManager.duplicateMaterial(base_file)
                if(material_id == "")
                {
                    return
                }
                if(Cura.MachineManager.hasMaterials)
                {
                    Cura.MachineManager.setActiveMaterial(material_id)
                }
                base.objectList.currentIndex = base.getIndexById(material_id);
            }
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Remove");
            iconName: "list-remove";
            enabled: base.currentItem != null && !base.currentItem.readOnly && !Cura.ContainerManager.isContainerUsed(base.currentItem.id)
            onClicked:
            {
                forceActiveFocus();
                confirmDialog.open();
            }
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Import");
            iconName: "document-import";
            onClicked:
            {
                forceActiveFocus();
                importDialog.open();
            }
            visible: true;
        },
        Button
        {
            text: catalog.i18nc("@action:button", "Export")
            iconName: "document-export"
            onClicked:
            {
                forceActiveFocus();
                exportDialog.open();
            }
            enabled: currentItem != null
        }
    ]

    Item {
        visible: base.currentItem != null
        anchors.fill: parent

        Item
        {
            id: profileName

            width: parent.width;
            height: childrenRect.height

            Label { text: materialProperties.name; font: UM.Theme.getFont("large"); }
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

            editingEnabled: base.currentItem != null && !base.currentItem.readOnly

            properties: materialProperties
            containerId: base.currentItem != null ? base.currentItem.id : ""

            property alias pane: base
        }

        QtObject
        {
            id: materialProperties

            property string guid: "00000000-0000-0000-0000-000000000000"
            property string name: "Unknown";
            property string profile_type: "Unknown";
            property string supplier: "Unknown";
            property string material_type: "Unknown";

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

        UM.ConfirmRemoveDialog
        {
            id: confirmDialog
            object: base.currentItem != null ? base.currentItem.name : ""
            onYes:
            {
                // A material container can actually be multiple items, so we need to find (and remove) all of them.
                var base_file = Cura.ContainerManager.getContainerMetaDataEntry(base.currentItem.id, "base_file")
                if(base_file == "")
                {
                    base_file = base.currentItem.id
                }
                var guid = Cura.ContainerManager.getContainerMetaDataEntry(base.currentItem.id, "GUID")
                var containers = Cura.ContainerManager.findInstanceContainers({"GUID": guid, "base_file": base_file, "type": "material"})
                for(var i in containers)
                {
                    Cura.ContainerManager.removeContainer(containers[i])
                }
                if(base.objectList.currentIndex > 0)
                {
                    base.objectList.currentIndex--;
                }
                currentItem = base.model.getItem(base.objectList.currentIndex) // Refresh the current item.
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
                messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tags <filename> or <message>!", "Could not import material <filename>%1</filename>: <message>%2</message>").arg(fileUrl).arg(result.message)
                if(result.status == "success")
                {
                    messageDialog.icon = StandardIcon.Information
                    messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tag <filename>!", "Successfully imported material <filename>%1</filename>").arg(fileUrl)
                    currentItem = base.model.getItem(base.objectList.currentIndex)
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
                    messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tags <filename> and <message>!", "Failed to export material to <filename>%1</filename>: <message>%2</message>").arg(fileUrl).arg(result.message)
                    messageDialog.open()
                }
                else if(result.status == "success")
                {
                    messageDialog.icon = StandardIcon.Information
                    messageDialog.text = catalog.i18nc("@info:status Don't translate the XML tag <filename>!", "Successfully exported material to <filename>%1</filename>").arg(result.path)
                    messageDialog.open()
                }
                CuraApplication.setDefaultPath("dialog_material_path", folder)
            }
        }

        MessageDialog
        {
            id: messageDialog
        }

        UM.SettingPropertyProvider
        {
            id: materialDiameterProvider

            containerStackId: Cura.MachineManager.activeMachineId
            key: "material_diameter"
            watchedProperties: [ "value" ]
        }

        UM.I18nCatalog { id: catalog; name: "cura"; }
        SystemPalette { id: palette }
    }

    onCurrentItemChanged:
    {
        if(currentItem == null)
        {
            return
        }
        materialProperties.name = currentItem.name;
        materialProperties.guid = Cura.ContainerManager.getContainerMetaDataEntry(base.currentItem.id, "GUID");

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
                materialProperties.approximate_diameter = currentItem.metadata.approximate_diameter ? currentItem.metadata.approximate_diameter : "0";
            }
            else
            {
                materialProperties.density = 0.0;
                materialProperties.diameter = 0.0;
                materialProperties.approximate_diameter = "0";
            }

        }
    }
}
