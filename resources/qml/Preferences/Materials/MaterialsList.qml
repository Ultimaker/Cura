// Copyright (c) 2019 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: materialList
    height: childrenRect.height

    // Children
    UM.I18nCatalog { id: catalog; name: "cura"; }
    Cura.MaterialBrandsModel
    {
        id: materialsModel
        extruderPosition: Cura.ExtruderManager.activeExtruderIndex
    }

    Cura.FavoriteMaterialsModel
    {
        id: favoriteMaterialsModel
        extruderPosition: Cura.ExtruderManager.activeExtruderIndex
    }

    Cura.GenericMaterialsModel
    {
        id: genericMaterialsModel
        extruderPosition: Cura.ExtruderManager.activeExtruderIndex
    }

    property var currentType: null
    property var currentBrand: null
    property var expandedBrands: UM.Preferences.getValue("cura/expanded_brands").split(";")
    property var expandedTypes: UM.Preferences.getValue("cura/expanded_types").split(";")

    // Store information about which parts of the tree are expanded
    function persistExpandedCategories()
    {
        UM.Preferences.setValue("cura/expanded_brands", materialList.expandedBrands.join(";"))
        UM.Preferences.setValue("cura/expanded_types", materialList.expandedTypes.join(";"))
    }

    // Expand the list of materials in order to select the current material
    function expandActiveMaterial(search_root_id)
    {
        if (search_root_id == "")
        {
            // When this happens it means that the information of one of the materials has changed, so the model
            // was updated and the list has to highlight the current item.
            var currentItemId = base.currentItem == null ? "" : base.currentItem.root_material_id
            search_root_id = currentItemId
        }
        for (var material_idx = 0; material_idx < genericMaterialsModel.count; material_idx++)
        {
            var material = genericMaterialsModel.getItem(material_idx)
            if (material.root_material_id == search_root_id)
            {
                if (materialList.expandedBrands.indexOf("Generic") == -1)
                {
                    materialList.expandedBrands.push("Generic")
                }
                materialList.currentBrand = "Generic"
                base.currentItem = material
                persistExpandedCategories()
                return true
            }
        }
        for (var brand_idx = 0; brand_idx < materialsModel.count; brand_idx++)
        {
            var brand = materialsModel.getItem(brand_idx)
            var types_model = brand.material_types
            for (var type_idx = 0; type_idx < types_model.count; type_idx++)
            {
                var type = types_model.getItem(type_idx)
                var colors_model = type.colors
                for (var material_idx = 0; material_idx < colors_model.count; material_idx++)
                {
                    var material = colors_model.getItem(material_idx)
                    if (material.root_material_id == search_root_id)
                    {
                        if (materialList.expandedBrands.indexOf(brand.name) == -1)
                        {
                            materialList.expandedBrands.push(brand.name)
                        }
                        materialList.currentBrand = brand.name
                        if (materialList.expandedTypes.indexOf(brand.name + "_" + type.name) == -1)
                        {
                            materialList.expandedTypes.push(brand.name + "_" + type.name)
                        }
                        materialList.currentType = brand.name + "_" + type.name
                        base.currentItem = material
                        persistExpandedCategories()
                        return true
                    }
                }
            }
        }
        base.currentItem = null
        return false
    }

    function updateAfterModelChanges()
    {
        var correctlyExpanded = materialList.expandActiveMaterial(base.newRootMaterialIdToSwitchTo)
        if (correctlyExpanded)
        {
            if (base.toActivateNewMaterial)
            {
                var position = Cura.ExtruderManager.activeExtruderIndex
                Cura.MachineManager.setMaterialById(position, base.newRootMaterialIdToSwitchTo)
            }
            base.newRootMaterialIdToSwitchTo = ""
            base.toActivateNewMaterial = false
        }
    }

    Connections
    {
        target: materialsModel
        function onItemsChanged() { updateAfterModelChanges() }
    }

    Connections
    {
        target: genericMaterialsModel
        function onItemsChanged() { updateAfterModelChanges() }
    }
    
    Column
    {
        width: materialList.width
        height: childrenRect.height

        MaterialsBrandSection
        {
            id: favoriteSection
            sectionName: "Favorites"
            elementsModel: favoriteMaterialsModel
            hasMaterialTypes: false
        }

        MaterialsBrandSection
        {
            id: genericSection
            sectionName: "Generic"
            elementsModel: genericMaterialsModel
            hasMaterialTypes: false
        }

        Repeater
        {
            model: materialsModel
            delegate: MaterialsBrandSection
            {
                id: brandSection
                sectionName: model.name
                elementsModel: model.material_types
                hasMaterialTypes: true
            }
        }
    }
}