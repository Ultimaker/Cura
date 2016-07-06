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
        }
        MenuItem
        {
            text:
            {
                var result = model.name

                if(model.metadata.brand != undefined && model.metadata.brand != "Generic")
                {
                    result = model.metadata.brand + " " + result
                }

                if(model.metadata.color_name != undefined && model.metadata.color_name != "Generic")
                {
                    result = result + " (%1)".arg(model.metadata.color_name)
                }

                return result
            }
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

    ExclusiveGroup { id: group }

    MenuSeparator { }

    MenuItem { action: Cura.Actions.manageMaterials }
}
