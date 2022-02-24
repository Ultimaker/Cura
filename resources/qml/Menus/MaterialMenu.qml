// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4

import UM 1.5 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    id: materialMenu
    title: catalog.i18nc("@label:category menu label", "Material")

    property int extruderIndex: 0
    property string currentRootMaterialId:
    {
        var value = Cura.MachineManager.currentRootMaterialId[extruderIndex]
        return (value === undefined) ? "" : value
    }
    property var activeExtruder:
    {
        var activeMachine = Cura.MachineManager.activeMachine
        return (activeMachine === null) ? null : activeMachine.extruderList[extruderIndex]
    }
    property bool isActiveExtruderEnabled: (activeExtruder === null || activeExtruder === undefined) ? false : activeExtruder.isEnabled

    property string activeMaterialId: (activeExtruder === null || activeExtruder === undefined) ? "" : activeExtruder.material.id
    property bool updateModels: true
    Cura.FavoriteMaterialsModel
    {
        id: favoriteMaterialsModel
        extruderPosition: materialMenu.extruderIndex
        enabled: updateModels
    }

    Cura.GenericMaterialsModel
    {
        id: genericMaterialsModel
        extruderPosition: materialMenu.extruderIndex
        enabled: updateModels
    }

    Cura.MaterialBrandsModel
    {
        id: brandModel
        extruderPosition: materialMenu.extruderIndex
        enabled: updateModels
    }

    Cura.MenuItem
    {
        text: catalog.i18nc("@label:category menu label", "Favorites")
        enabled: false
        visible: favoriteMaterialsModel.items.length > 0
    }

    Instantiator
    {
        model: favoriteMaterialsModel
        delegate: Cura.MenuItem
        {
            text: model.brand + " " + model.name
            checkable: true
            enabled: isActiveExtruderEnabled
            checked: model.root_material_id === materialMenu.currentRootMaterialId
            onTriggered: Cura.MachineManager.setMaterial(extruderIndex, model.container_node)
        }
        onObjectAdded: materialMenu.insertItem(index + 1, object)
        onObjectRemoved: materialMenu.removeItem(index)
    }

    Cura.MenuSeparator { visible: favoriteMaterialsModel.items.length > 0}

    Cura.Menu
    {
        id: genericMenu
        title: catalog.i18nc("@label:category menu label", "Generic")

        Instantiator
        {
            model: genericMaterialsModel
            delegate: Cura.MenuItem
            {
                text: model.name
                checkable: true
                enabled: isActiveExtruderEnabled
                checked: model.root_material_id === materialMenu.currentRootMaterialId
                onTriggered: Cura.MachineManager.setMaterial(extruderIndex, model.container_node)
            }
            onObjectAdded: genericMenu.insertItem(index, object)
            onObjectRemoved: genericMenu.removeItem(index)
        }
    }

    Cura.MenuSeparator {}

    Instantiator
    {
        model: brandModel
        Cura.Menu
        {
            id: brandMenu
            title: brandName
            property string brandName: model.name
            property var brandMaterials: model.material_types

            Instantiator
            {
                model: brandMaterials
                delegate: Menu
                {
                    id: brandMaterialsMenu
                    title: materialName
                    property string materialName: model.name
                    property var brandMaterialColors: model.colors

                    Instantiator
                    {
                        model: brandMaterialColors
                        delegate: Cura.MenuItem
                        {
                            text: model.name
                            checkable: true
                            enabled: isActiveExtruderEnabled
                            checked: model.id === materialMenu.activeMaterialId

                            onTriggered: Cura.MachineManager.setMaterial(extruderIndex, model.container_node)
                        }
                        onObjectAdded: brandMaterialsMenu.insertItem(index, object)
                        onObjectRemoved: brandMaterialsMenu.removeItem(object)
                    }
                }
                onObjectAdded: brandMenu.insertMenu(index, object)
                onObjectRemoved: brandMenu.removeMenu(object)
            }
        }
        onObjectAdded: materialMenu.insertMenu(index + 4, object)
        onObjectRemoved: materialMenu.removeMenu(object)
    }

    Cura.MenuSeparator {}

    Cura.MenuItem
    {
        action: Cura.Actions.manageMaterials
    }

    Cura.MenuSeparator {}

    Cura.MenuItem
    {
        action: Cura.Actions.marketplaceMaterials
    }
}
