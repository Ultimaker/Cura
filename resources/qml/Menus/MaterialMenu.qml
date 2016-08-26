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
        model: UM.InstanceContainersModel
        {
            filter: materialFilter("Generic")
        }
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
            property string brandName: model.brandName
            property var brandMaterials: model.materials

            Instantiator
            {
                model: brandMaterials
                Menu
                {
                    id: brandMaterialsMenu
                    title: materialName
                    property string materialName: model.materialName

                    Instantiator
                    {
                        model: UM.InstanceContainersModel
                        {
                            filter: materialFilter(brandMenu.brandName, brandMaterialsMenu.materialName)
                        }
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
        id: brandModel
        Component.onCompleted: populateBrandModel()
    }

    //: Model used to populate the brandModel
    UM.InstanceContainersModel
    {
        id: materialsModel
        filter: materialFilter()
        onDataChanged: populateBrandModel()
    }

    ExclusiveGroup { id: group }

    MenuSeparator { }

    MenuItem { action: Cura.Actions.manageMaterials }

    function materialFilter(brand, material)
    {
        var result = { "type": "material" };
        if(brand)
        {
            result.brand = brand;
        }
        if(material)
        {
            result.material = material;
        }
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

    function populateBrandModel()
    {
        // Create a structure of unique brands and their material-types
        var items = materialsModel.items;
        var materialsByBrand = {}
        for (var i in items) {
            var brandName = items[i]["metadata"]["brand"];
            var materialName = items[i]["metadata"]["material"];

            if (brandName == "Generic")
            {
                continue;
            }
            if (!materialsByBrand.hasOwnProperty(brandName))
            {
                materialsByBrand[brandName] = [];
            }
            if (materialsByBrand[brandName].indexOf(materialName) == -1)
            {
                materialsByBrand[brandName].push(materialName);
            }
        }

        brandModel.clear();
        for (var brand in materialsByBrand)
        {
            var materialsByBrandModel = [];
            var materials = materialsByBrand[brand];
            for (var material in materials)
            {
                materialsByBrandModel.push({materialName: materials[material]})
            }
            brandModel.append({
                brandName: brand,
                materials: materialsByBrandModel
            });
        }
    }
}
