// Copyright (c) 2018 Ultimaker B.V.
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
    width: materialScrollView.width - 17
    height: childrenRect.height

    // Children
    UM.I18nCatalog { id: catalog; name: "cura"; }
    Cura.MaterialBrandsModel { id: materialsModel }
    Cura.FavoriteMaterialsModel { id: favoriteMaterialsModel }
    Cura.GenericMaterialsModel { id: genericMaterialsModel }

    property var currentType: null
    property var currentBrand: null
    property var expandedBrands: UM.Preferences.getValue("cura/expanded_brands").split(";")
    property var expandedTypes: UM.Preferences.getValue("cura/expanded_types").split(";")
    
    function expandActiveMaterial(search_root_id)
    {
        for (var n = 0; n < genericMaterialsModel.rowCount(); n++)
        {
            var material = genericMaterialsModel.getItem(n);
            if (material.root_material_id == search_root_id)
            {
                if (materialList.expandedBrands.indexOf("Generic") == -1)
                {
                    materialList.expandedBrands.push("Generic");
                    materialList.currentBrand = "Generic"
                }
            }
        }
        for (var i = 0; i < materialsModel.rowCount(); i++)
        {
            var brand = materialsModel.getItem(i);
            var types_model = brand.material_types;

            for (var j = 0; j < types_model.rowCount(); j++)
            {
                var type = types_model.getItem(j);
                var colors_model = type.colors;
                for (var k = 0; k < colors_model.rowCount(); k++)
                {
                    var material = colors_model.getItem(k);
                    if (material.root_material_id == search_root_id)
                    {
                        if (materialList.expandedBrands.indexOf(brand.name) == -1)
                        {
                            materialList.expandedBrands.push(brand.name);
                            materialList.currentBrand = brand.name
                        }
                        if (materialList.expandedTypes.indexOf(brand.name + "_" + type.name) == -1)
                        {
                            materialList.expandedTypes.push(brand.name + "_" + type.name)
                            materialList.currentType = brand.name + "_" + type.name
                        }
                    }
                }
            }
        }
        UM.Preferences.setValue("cura/expanded_brands", materialList.expandedBrands.join(";"));
        UM.Preferences.setValue("cura/expanded_types", materialList.expandedTypes.join(";"));
    }

//    Connections
//    {
//        target: materialsModel
//        onItemsChanged:
//        {
//            var currentItemId = base.hasCurrentItem ? base.currentItem.root_material_id : ""
//            var position = Cura.ExtruderManager.activeExtruderIndex
//            console.log("!!!!!!!!!!!!!!!!!!! on items changed:", base.newRootMaterialIdToSwitchTo)
//
//            // try to pick the currently selected item; it may have been moved
//            if (base.newRootMaterialIdToSwitchTo == "")
//            {
//                console.log("material id is empty, setting to ", currentItemId)
//                base.newRootMaterialIdToSwitchTo = currentItemId
//            }
//
//            console.log("PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP", materialsModel.rowCount())
//            for (var brand_idx = 0; brand_idx < materialsModel.rowCount(); ++brand_idx)
//            {
//                var brand = materialsModel.getItem(brand_idx)
//                console.log(item.root_material_id, "=", base.newRootMaterialIdToSwitchTo)
//
//                for (var type_idx = 0; type_idx < brand.material_types.rowCount(); ++type_idx)
//                {
//                    var type = brand.material_types.getItem(type_idx)
//                    if (type.root_material_id == base.newRootMaterialIdToSwitchTo)
//                    {
//                        // Switch to the newly created profile if needed
//                        base.currentItem = item
//    //                    materialDetailsPanel.activateDetailsWithIndex(materialListView.currentIndex)
//    //                    if (base.toActivateNewMaterial)
//    //                    {
//    //                        Cura.MachineManager.setMaterial(position, item.container_node)
//    //                    }
//                        base.newRootMaterialIdToSwitchTo = ""
//                        base.toActivateNewMaterial = false
//                        return
//                    }
//                }
//            }
//
//            // If the new id can't be found, then do nothing
////            materialListView.currentIndex = 0
////            materialListView.activateDetailsWithIndex(materialListView.currentIndex)
////            if (base.toActivateNewMaterial)
////            {
////                Cura.MachineManager.setMaterial(position, materialsModel.getItem(0).container_node)
////            }
//            base.newRootMaterialIdToSwitchTo = ""
//            base.toActivateNewMaterial = false
//        }
//    }
    
    Column
    {
        Rectangle
        {
            property var expanded: true

            id: favorites_section
            height: childrenRect.height
            width: materialList.width
            Rectangle
            {
                id: favorites_header_background
                color: UM.Theme.getColor("favorites_header_bar")
                anchors.fill: favorites_header
            }
            Row
            {
                id: favorites_header
                Label
                {
                    id: favorites_name
                    text: "Favorites"
                    height: UM.Theme.getSize("favorites_row").height
                    width: materialList.width - UM.Theme.getSize("favorites_button").width
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 4
                }
                Button
                {
                    text: ""
                    implicitWidth: UM.Theme.getSize("favorites_button").width
                    implicitHeight: UM.Theme.getSize("favorites_button").height
                    UM.RecolorImage {
                        anchors
                        {
                            verticalCenter: parent.verticalCenter
                            horizontalCenter: parent.horizontalCenter
                        }
                        width: UM.Theme.getSize("standard_arrow").width
                        height: UM.Theme.getSize("standard_arrow").height
                        sourceSize.width: width
                        sourceSize.height: height
                        color: "black"
                        source: favorites_section.expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
                    }
                    style: ButtonStyle
                    {
                        background: Rectangle
                        {
                            anchors.fill: parent
                            color: "transparent"
                        }
                    }
                }
            }
            MouseArea
            {
                anchors.fill: favorites_header
                onPressed:
                {
                    favorites_section.expanded = !favorites_section.expanded
                }
            }
            Column
            {
                anchors.top: favorites_header.bottom
                anchors.left: parent.left
                width: materialList.width
                height: favorites_section.expanded ? childrenRect.height : 0
                visible: favorites_section.expanded
                Repeater
                {
                    model: favoriteMaterialsModel
                    delegate: MaterialsSlot {
                        material: model
                    }
                }
            }
        }
        Rectangle
        {
            property var expanded: materialList.expandedBrands.indexOf("Generic") > -1

            id: generic_section
            height: childrenRect.height
            width: materialList.width
            Rectangle
            {
                id: generic_header_background
                color: UM.Theme.getColor("favorites_header_bar")
                anchors.fill: generic_header
            }
            Row
            {
                id: generic_header
                Label
                {
                    id: generic_name
                    text: "Generic"
                    height: UM.Theme.getSize("favorites_row").height
                    width: materialList.width - UM.Theme.getSize("favorites_button").width
                    verticalAlignment: Text.AlignVCenter
                    leftPadding: 4
                }
                Button
                {
                    text: ""
                    implicitWidth: UM.Theme.getSize("favorites_button").width
                    implicitHeight: UM.Theme.getSize("favorites_button").height
                    UM.RecolorImage {
                        anchors
                        {
                            verticalCenter: parent.verticalCenter
                            horizontalCenter: parent.horizontalCenter
                        }
                        width: UM.Theme.getSize("standard_arrow").width
                        height: UM.Theme.getSize("standard_arrow").height
                        sourceSize.width: width
                        sourceSize.height: height
                        color: "black"
                        source: generic_section.expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
                    }
                    style: ButtonStyle
                    {
                        background: Rectangle
                        {
                            anchors.fill: parent
                            color: "transparent"
                        }
                    }
                }
            }
            MouseArea
            {
                anchors.fill: generic_header
                onPressed:
                {
                    const index = materialList.expandedBrands.indexOf("Generic")

                    if (index > -1)
                    {
                        // Remove it
                        materialList.expandedBrands.splice(index, 1)
                        generic_section.expanded = false
                    }
                    else
                    {
                        // Add it
                        materialList.expandedBrands.push("Generic")
                        generic_section.expanded = true
                    }
                }
            }
            Column
            {
                anchors.top: generic_header.bottom
                width: materialList.width
                anchors.left: parent.left
                height: generic_section.expanded ? childrenRect.height : 0
                visible: generic_section.expanded

                Repeater
                {
                    model: genericMaterialsModel
                    delegate: MaterialsSlot
                    {
                        material: model
                    }
                }
            }
        }
        Repeater
        {
            id: brand_list
            model: materialsModel
            delegate: MaterialsBrandSection {}
        }
    }
}