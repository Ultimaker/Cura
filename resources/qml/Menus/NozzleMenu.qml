// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: "Nozzle"

    property int extruderIndex: 0
    property bool printerConnected: Cura.MachineManager.printerOutputDevices.length != 0
    property bool isClusterPrinter:
    {
        if(Cura.MachineManager.printerOutputDevices.length == 0)
        {
            return false;
        }
        var clusterSize = Cura.MachineManager.printerOutputDevices[0].clusterSize;
        // This is not a cluster printer or the cluster it is just one printer
        if(clusterSize == undefined || clusterSize == 1)
        {
            return false;
        }
        return true;
    }

    // TODO: single instance??
    Cura.NozzleModel
    {
        id: nozzleModel
    }

    Instantiator
    {
        model: nozzleModel

        MenuItem
        {
            text: model.hotend_name
            checkable: true
            checked: Cura.MachineManager.activeVariantId == model.hotend_name
            exclusiveGroup: group
            onTriggered: {
                var position = Cura.ExtruderManager.activeExtruderIndex;
                Cura.MachineManager.setVariantGroup(position, model.container_node);
            }
            visible: true
        }

        onObjectAdded: menu.insertItem(index, object);
        onObjectRemoved: menu.removeItem(object);
    }
    /*
    Instantiator
    {
        id: nozzleInstantiator
        model: UM.InstanceContainersModel
        {
            filter:
            {
                var filter_dict =
                {
                    "type": "variant",
                    "definition": Cura.MachineManager.activeQualityDefinitionId //Only show variants of this machine
                }
                if (Cura.MachineManager.hasVariantBuildplates)
                {
                    filter_dict["hardware_type"] = "nozzle"
                }

                return filter_dict
            }
        }
        MenuItem {
            text: model.name
            checkable: true
            checked: model.id == Cura.MachineManager.allActiveVariantIds[Cura.ExtruderManager.extruderIds[extruderIndex]]
            exclusiveGroup: group
            onTriggered:
            {
                var activeExtruderIndex = Cura.ExtruderManager.activeExtruderIndex;
                Cura.ExtruderManager.setActiveExtruderIndex(extruderIndex);
                Cura.MachineManager.setActiveVariant(model.id);
                Cura.ExtruderManager.setActiveExtruderIndex(activeExtruderIndex);
            }
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    } */

    ExclusiveGroup { id: group }
}
