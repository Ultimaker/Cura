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
    addText: catalog.i18nc("@action:button", "Duplicate")

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

    onActivateObject: Cura.MachineManager.setActiveMaterial(currentItem.id)

    activateEnabled: currentItem != null ? currentItem.id != Cura.MachineManager.activeMaterialId : false;
    addEnabled: currentItem != null;
    removeEnabled: currentItem != null ? !currentItem.readOnly : false;
    renameEnabled: currentItem != null ? !currentItem.readOnly : false;

    scrollviewCaption: "Printer: %1, Nozzle: %2".arg(Cura.MachineManager.activeMachineName).arg(Cura.MachineManager.activeVariantName)
    detailsVisible: true

    section.property: "section"
    section.delegate: Label { text: section }

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

                checkable: true
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

            editingEnabled: editButton.checked;

            properties: materialProperties
            containerId: base.currentItem.id
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
