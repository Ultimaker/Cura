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

    MenuItem
    {
        id: automaticNozzle
        text:
        {
            if(printerConnected && Cura.MachineManager.printerOutputDevices[0].hotendIds.length > extruderIndex)
            {
                var nozzleName = Cura.MachineManager.printerOutputDevices[0].hotendIds[extruderIndex];
                return catalog.i18nc("@title:menuitem %1 is the nozzle currently loaded in the printer", "Automatic: %1").arg(nozzleName);
            }
            return "";
        }
        visible: printerConnected && Cura.MachineManager.printerOutputDevices[0].hotendIds.length > extruderIndex
        onTriggered:
        {
            var activeExtruderIndex = ExtruderManager.activeExtruderIndex;
            ExtruderManager.setActiveExtruderIndex(extruderIndex);
            var hotendId = Cura.MachineManager.printerOutputDevices[0].hotendIds[extruderIndex];
            var itemIndex = nozzleInstantiator.model.find("name", hotendId);
            if(itemIndex > -1)
            {
                Cura.MachineManager.setActiveVariant(nozzleInstantiator.model.getItem(itemIndex).id);
            }
            ExtruderManager.setActiveExtruderIndex(activeExtruderIndex);
        }
    }

    MenuSeparator
    {
        visible: automaticNozzle.visible
    }

    Instantiator
    {
        id: nozzleInstantiator
        model: UM.InstanceContainersModel
        {
            filter:
            {
                "type": "variant",
                "definition": Cura.MachineManager.activeQualityDefinitionId //Only show variants of this machine
            }
        }
        MenuItem {
            text: model.name
            checkable: true
            checked: model.id == Cura.MachineManager.allActiveVariantIds[ExtruderManager.extruderIds[extruderIndex]]
            exclusiveGroup: group
            onTriggered:
            {
                var activeExtruderIndex = ExtruderManager.activeExtruderIndex;
                ExtruderManager.setActiveExtruderIndex(extruderIndex);
                Cura.MachineManager.setActiveVariant(model.id);
                ExtruderManager.setActiveExtruderIndex(activeExtruderIndex);
            }
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    ExclusiveGroup { id: group }
}
