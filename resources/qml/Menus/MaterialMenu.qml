// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: "Material"

    property int extruderIndex: 0
    property bool printerConnected: Cura.MachineManager.printerOutputDevices.length != 0

    UM.SettingPropertyProvider
    {
        id: materialDiameterProvider

        containerStackId: Cura.MachineManager.activeMachineId
        key: "material_diameter"
        watchedProperties: [ "value" ]
    }

    MenuItem
    {
        id: automaticMaterial
        text:
        {
            if(printerConnected && Cura.MachineManager.printerOutputDevices[0].materialNames.length > extruderIndex)
            {
                var materialName = Cura.MachineManager.printerOutputDevices[0].materialNames[extruderIndex];
                return catalog.i18nc("@title:menuitem %1 is the automatically selected material", "Automatic: %1").arg(materialName);
            }
            return "";
        }
        visible: printerConnected && Cura.MachineManager.printerOutputDevices[0].materialNames.length > extruderIndex
        onTriggered:
        {
            var activeExtruderIndex = ExtruderManager.activeExtruderIndex;
            ExtruderManager.setActiveExtruderIndex(extruderIndex);
            var materialId = Cura.MachineManager.printerOutputDevices[0].materialIds[extruderIndex];
            var items = materialsModel.items;
            // materialsModel.find cannot be used because we need to look inside the metadata property of items
            for(var i in items)
            {
                if (items[i]["metadata"]["GUID"] == materialId)
                {
                    Cura.MachineManager.setActiveMaterial(items[i].id);
                    break;
                }
            }
            ExtruderManager.setActiveExtruderIndex(activeExtruderIndex);
        }
    }

    MenuSeparator
    {
        visible: automaticMaterial.visible
    }

    Instantiator
    {
        model: genericMaterialsModel
        MenuItem
        {
            text: model.name
            checkable: true
            checked: model.id == Cura.MachineManager.allActiveMaterialIds[ExtruderManager.extruderIds[extruderIndex]]
            exclusiveGroup: group
            onTriggered:
            {
                var activeExtruderIndex = ExtruderManager.activeExtruderIndex;
                ExtruderManager.setActiveExtruderIndex(extruderIndex);
                Cura.MachineManager.setActiveMaterial(model.id);
                ExtruderManager.setActiveExtruderIndex(activeExtruderIndex);
            }
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }
    MenuSeparator { }
    Instantiator
    {
        model: brandModel
        Menu
        {
            id: brandMenu
            title: brandName
            property string brandName: model.name
            property var brandMaterials: model.materials

            Instantiator
            {
                model: brandMaterials
                Menu
                {
                    id: brandMaterialsMenu
                    title: materialName
                    property string materialName: model.name
                    property var brandMaterialColors: model.colors

                    Instantiator
                    {
                        model: brandMaterialColors
                        MenuItem
                        {
                            text: model.name
                            checkable: true
                            checked: model.id == Cura.MachineManager.allActiveMaterialIds[ExtruderManager.extruderIds[extruderIndex]]
                            exclusiveGroup: group
                            onTriggered:
                            {
                                var activeExtruderIndex = ExtruderManager.activeExtruderIndex;
                                ExtruderManager.setActiveExtruderIndex(extruderIndex);
                                Cura.MachineManager.setActiveMaterial(model.id);
                                ExtruderManager.setActiveExtruderIndex(activeExtruderIndex);
                            }
                        }
                        onObjectAdded: brandMaterialsMenu.insertItem(index, object)
                        onObjectRemoved: brandMaterialsMenu.removeItem(object)
                    }
                }
                onObjectAdded: brandMenu.insertItem(index, object)
                onObjectRemoved: brandMenu.removeItem(object)
            }
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    ListModel
    {
        id: genericMaterialsModel
        Component.onCompleted: populateMenuModels()
    }

    ListModel
    {
        id: brandModel
    }

    //: Model used to populate the brandModel
    UM.InstanceContainersModel
    {
        id: materialsModel
        filter: materialFilter()
        onModelReset: populateMenuModels()
        onDataChanged: populateMenuModels()
    }

    ExclusiveGroup { id: group }

    MenuSeparator { }

    MenuItem { action: Cura.Actions.manageMaterials }

    function materialFilter()
    {
        var result = { "type": "material", "approximate_diameter": Math.round(materialDiameterProvider.properties.value).toString() };
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
        return result;
    }

    function populateMenuModels()
    {
        // Create a structure of unique brands and their material-types
        genericMaterialsModel.clear()
        brandModel.clear();

        var items = materialsModel.items;
        var materialsByBrand = {};
        for (var i in items) {
            var brandName = items[i]["metadata"]["brand"];
            var materialName = items[i]["metadata"]["material"];

            if (brandName == "Generic")
            {
                // Add to top section
                var materialId = items[i].id;
                genericMaterialsModel.append({
                    id:materialId,
                    name:items[i].name
                });
            }
            else
            {
                // Add to per-brand, per-material menu
                if (!materialsByBrand.hasOwnProperty(brandName))
                {
                    materialsByBrand[brandName] = {};
                }
                if (!materialsByBrand[brandName].hasOwnProperty(materialName))
                {
                    materialsByBrand[brandName][materialName] = [];
                }
                materialsByBrand[brandName][materialName].push({
                    id: items[i].id,
                    name: items[i].name
                });
            }
        }

        for (var brand in materialsByBrand)
        {
            var materialsByBrandModel = [];
            var materials = materialsByBrand[brand];
            for (var material in materials)
            {
                materialsByBrandModel.push({
                    name: material,
                    colors: materials[material]
                })
            }
            brandModel.append({
                name: brand,
                materials: materialsByBrandModel
            });
        }
    }
}
