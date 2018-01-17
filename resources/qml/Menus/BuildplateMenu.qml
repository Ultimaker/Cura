// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: "Build plate"

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

    MenuItem
    {
        id: automaticBuildplate
        text:
        {
            if(printerConnected && Cura.MachineManager.printerOutputDevices[0].buildplateId != "" && !isClusterPrinter)
            {
                var buildplateName = Cura.MachineManager.printerOutputDevices[0].buildplateId
                return catalog.i18nc("@title:menuitem %1 is the buildplate currently loaded in the printer", "Automatic: %1").arg(buildplateName)
            }
            return ""
        }
        visible: printerConnected && Cura.MachineManager.printerOutputDevices[0].buildplateId != "" && !isClusterPrinter
        onTriggered:
        {
            var buildplateId = Cura.MachineManager.printerOutputDevices[0].buildplateId
            var itemIndex = buildplateInstantiator.model.find("name", buildplateId)
            if(itemIndex > -1)
            {
                Cura.MachineManager.setActiveVariantBuildplate(buildplateInstantiator.model.getItem(itemIndex).id)
            }
        }
    }

    MenuSeparator
    {
        visible: automaticBuildplate.visible
    }

    Instantiator
    {
        id: buildplateInstantiator
        model: UM.InstanceContainersModel
        {
            filter:
            {
                "type": "variant",
                "hardware_type": "buildplate",
                "definition": Cura.MachineManager.activeDefinitionId //Only show variants of this machine
            }
        }
        MenuItem {
            text: model.name
            checkable: true
            checked: model.id == Cura.MachineManager.globalVariantId
            exclusiveGroup: group
            onTriggered:
            {
                Cura.MachineManager.setActiveVariantBuildplate(model.id);
            }
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    ExclusiveGroup { id: group }
}
