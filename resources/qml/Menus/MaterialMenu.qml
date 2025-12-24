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

    Cura.MaterialBrandsModel
    {
        id: brandModel
        extruderPosition: materialMenu.extruderIndex
        enabled: updateModels
    }

    Instantiator
    {
        model: brandModel
        delegate: Cura.MaterialBrandMenu
        {
            materialTypesModel: model
        }
        onObjectAdded: function(index, object) { materialMenu.insertItem(index + 4, object)}
        onObjectRemoved: function(index, object) { materialMenu.removeItem(index) }
    }
}
