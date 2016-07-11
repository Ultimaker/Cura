// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

 Menu
{
    id: menu

    Instantiator
    {
        model: UM.InstanceContainersModel
        {
            filter: menu.getFilter({ "read_only": true });
        }

        MenuItem
        {
            text: model.name
            checkable: true
            checked: Cura.MachineManager.activeQualityId == model.id
            exclusiveGroup: group
            onTriggered: Cura.MachineManager.setActiveQuality(model.id)
        }

        onObjectAdded: menu.insertItem(index, object);
        onObjectRemoved: menu.removeItem(object);
    }

    MenuSeparator { id: customSeparator }

    Instantiator
    {
        id: customProfileInstantiator
        model: UM.InstanceContainersModel
        {
            filter: menu.getFilter({ "read_only": false });
            onModelReset: customSeparator.visible = rowCount() > 0
        }

        MenuItem
        {
            text: model.name
            checkable: true
            checked: Cura.MachineManager.activeQualityId == model.id
            exclusiveGroup: group
            onTriggered: Cura.MachineManager.setActiveQuality(model.id)
        }

        onObjectAdded:
        {
            customSeparator.visible = model.rowCount() > 0;
            menu.insertItem(index, object);
        }
        onObjectRemoved:
        {
            customSeparator.visible = model.rowCount() > 0;
            menu.removeItem(object);
        }
    }

    ExclusiveGroup { id: group; }

    MenuSeparator { id: profileMenuSeparator }

    MenuItem { action: Cura.Actions.addProfile }
    MenuItem { action: Cura.Actions.updateProfile }
    MenuItem { action: Cura.Actions.resetProfile }
    MenuSeparator { }
    MenuItem { action: Cura.Actions.manageProfiles }

    function getFilter(initial_conditions)
    {
        var result = initial_conditions;
        result.type = "quality"

        if(Cura.MachineManager.filterQualityByMachine)
        {
            result.definition = Cura.MachineManager.activeDefinitionId;
            if(Cura.MachineManager.hasMaterials)
            {
                result.material = Cura.MachineManager.activeMaterialId;
            }
        }
        else
        {
            result.definition = "fdmprinter"
        }
        return result
    }
}
