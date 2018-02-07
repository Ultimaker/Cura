// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.8
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu
    title: "Material"

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

    MenuItem
    {
        id: automaticMaterial
        text:
        {
            if(visible)
            {
                var materialName = Cura.MachineManager.printerOutputDevices[0].materialNames[extruderIndex];
                return catalog.i18nc("@title:menuitem %1 is the automatically selected material", "Automatic: %1").arg(materialName);
            }
            return "";
        }
        visible: printerConnected && Cura.MachineManager.printerOutputDevices[0].materialNames != undefined && Cura.MachineManager.printerOutputDevices[0].materialNames.length > extruderIndex && !isClusterPrinter
        onTriggered:
        {
            var materialId = Cura.MachineManager.printerOutputDevices[0].materialIds[extruderIndex];
            var items = materialsModel.items;
            for(var i in items)
            {
                if (items[i]["metadata"]["GUID"] == materialId)
                {
                    Cura.MachineManager.setActiveMaterial(items[i].id);
                    break;
                }
            }
        }
    }

    MenuSeparator
    {
        visible: automaticMaterial.visible
    }

    Instantiator
    {
        model: genericMaterialsModel
        MenuItem
        {
            text: model.name
            checkable: true
            checked: model.id == Cura.MachineManager.allActiveMaterialIds[Cura.ExtruderManager.extruderIds[extruderIndex]]
            exclusiveGroup: group
            onTriggered:
            {

                const container_id = model.id;
                // This workaround is done because of the application menus for materials and variants for multiextrusion printers.
                // The extruder menu would always act on the correspoding extruder only, instead of acting on the extruder selected in the UI.

                var activeExtruderIndex = Cura.ExtruderManager.activeExtruderIndex;
                //Cura.ExtruderManager.setActiveExtruderIndex(extruderIndex);
                //Cura.MachineManager.setActiveMaterial(container_id);
                //Cura.ExtruderManager.setActiveExtruderIndex(activeExtruderIndex);
                Cura.MachineManager.setMaterial(activeExtruderIndex, model.container_node);
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
            title: brandName
            property string brandName: model.name
            property var brandMaterials: model.materials

            Instantiator
            {
                model: brandMaterials
                Menu
                {
                    id: brandMaterialsMenu
                    title: materialName
                    property string materialName: model.name
                    property var brandMaterialColors: model.colors

                    Instantiator
                    {
                        model: brandMaterialColors
                        MenuItem
                        {
                            text: model.name
                            checkable: true
                            checked: model.id == Cura.MachineManager.allActiveMaterialIds[Cura.ExtruderManager.extruderIds[extruderIndex]]
                            exclusiveGroup: group
                            onTriggered:
                            {
                                const container_id = model.id;
                                // This workaround is done because of the application menus for materials and variants for multiextrusion printers.
                                // The extruder menu would always act on the correspoding extruder only, instead of acting on the extruder selected in the UI.
                                var activeExtruderIndex = Cura.ExtruderManager.activeExtruderIndex;
                                Cura.ExtruderManager.setActiveExtruderIndex(extruderIndex);
                                Cura.MachineManager.setActiveMaterial(container_id);
                                Cura.ExtruderManager.setActiveExtruderIndex(activeExtruderIndex);
                            }
                        }
                        onObjectAdded: brandMaterialsMenu.insertItem(index, object)
                        onObjectRemoved: brandMaterialsMenu.removeItem(object)
                    }
                }
                onObjectAdded: brandMenu.insertItem(index, object)
                onObjectRemoved: brandMenu.removeItem(object)
            }
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }

    Cura.GenericMaterialsModel
    {
        id: genericMaterialsModel
        //Component.onCompleted: populateMenuModels()
    }

    Cura.BrandMaterialsModel
    {
        id: brandModel
    }

    ExclusiveGroup { id: group }

    MenuSeparator { }

    MenuItem { action: Cura.Actions.manageMaterials }
}
