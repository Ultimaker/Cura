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
            title: model.brandName
            property string brand: model.brandName

            Instantiator
            {
                model: UM.InstanceContainersModel
                {
                    filter: materialFilter(brandMenu.brandName)
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

    function populateBrandModel()
    {
        var brands = materialsModel.getUniqueValues("brand")
        var material_types = materialsModel.getUniqueValues("material")
        brandModel.clear();
        for (var i in brands)
        {
            if(brands[i] != "Generic")
            {
                brandModel.append({
                    brandName: brands[i],
                    materials: []
                })
            }
        }
    }

    function materialFilter(brand, material)
    {
        var result = { "type": "material" }
        if(brand != undefined)
        {
            result.brand = brand
        }
        if(material != undefined)
        {
            result.material = material
        }
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
}
