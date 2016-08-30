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

    Instantiator
    {
        model: genericMaterialsModel
        MenuItem
        {
            text: model.name
            checkable: true;
            checked: model.id == Cura.MachineManager.activeMaterialId;
            exclusiveGroup: group;
            onTriggered:
            {
                Cura.MachineManager.setActiveMaterial(model.id);
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
                            checkable: true;
                            checked: model.id == Cura.MachineManager.activeMaterialId;
                            exclusiveGroup: group;
                            onTriggered:
                            {
                                Cura.MachineManager.setActiveMaterial(model.id);
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
    }

    ExclusiveGroup { id: group }

    MenuSeparator { }

    MenuItem { action: Cura.Actions.manageMaterials }

    function materialFilter()
    {
        var result = { "type": "material" };
        if(Cura.MachineManager.filterMaterialsByMachine)
        {
            result.definition = Cura.MachineManager.activeDefinitionId;
            if(Cura.MachineManager.hasVariants)
            {
                result.variant = Cura.MachineManager.activeVariantId;
            }
        }
        else
        {
            result.definition = "fdmprinter";
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
