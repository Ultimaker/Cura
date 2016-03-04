// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.1 as UM

Item
{
    id: base;
    // Machine Setup
    property Action addMachineAction;
    property Action configureMachinesAction;
    UM.I18nCatalog { id: catalog; name:"cura"}
    property int totalHeightHeader: childrenRect.height

    Rectangle {
        id: sidebarTabRow
        width: base.width
        height: 0
        anchors.top: parent.top
        color: UM.Theme.getColor("sidebar_header_bar")
    }

    Label{
        id: printjobTabLabel
        text: catalog.i18nc("@label:listbox","Print Job");
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width;
        anchors.top: sidebarTabRow.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width/100*45
        font: UM.Theme.getFont("large");
        color: UM.Theme.getColor("text")
    }

    Rectangle {
        id: machineSelectionRow
        width: base.width
        height: UM.Theme.getSize("sidebar_setup").height
        anchors.top: printjobTabLabel.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.horizontalCenter: parent.horizontalCenter

        Label{
            id: machineSelectionLabel
            //: Machine selection label
            text: catalog.i18nc("@label:listbox","Printer:");
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        ToolButton {
            id: machineSelection
            text: UM.MachineManager.activeMachineInstance;
            width: parent.width/100*55
            height: UM.Theme.getSize("setting_control").height
            tooltip: UM.MachineManager.activeMachineInstance;
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            style: UM.Theme.styles.sidebar_header_button

            menu: Menu
            {
                id: machineSelectionMenu
                Instantiator
                {
                    model: UM.MachineInstancesModel { }
                    MenuItem
                    {
                        text: model.name;
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: machineSelectionMenuGroup;
                        onTriggered: UM.MachineManager.setActiveMachineInstance(model.name);
                    }
                    onObjectAdded: machineSelectionMenu.insertItem(index, object)
                    onObjectRemoved: machineSelectionMenu.removeItem(object)
                }

                ExclusiveGroup { id: machineSelectionMenuGroup; }

                MenuSeparator { }

                MenuItem { action: base.addMachineAction; }
                MenuItem { action: base.configureMachinesAction; }
            }
        }
    }

    Rectangle {
        id: variantRow
        anchors.top: machineSelectionRow.bottom
        anchors.topMargin: UM.MachineManager.hasVariants ? UM.Theme.getSize("default_margin").height : 0
        width: base.width
        height: UM.MachineManager.hasVariants ? UM.Theme.getSize("sidebar_setup").height : 0
        visible: UM.MachineManager.hasVariants

        Label{
            id: variantLabel
            text: catalog.i18nc("@label","Nozzle:");
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width;
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width/100*45
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        ToolButton {
            id: variantSelection
            text: UM.MachineManager.activeMachineVariant
            width: parent.width/100*55
            height: UM.Theme.getSize("setting_control").height
            tooltip: UM.MachineManager.activeMachineVariant;
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            style: UM.Theme.styles.sidebar_header_button

            menu: Menu
            {
                id: variantsSelectionMenu
                Instantiator
                {
                    id: variantSelectionInstantiator
                    model: UM.MachineVariantsModel { id: variantsModel }
                    MenuItem
                    {
                        text: model.name;
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: variantSelectionMenuGroup;
                        onTriggered:
                        {
                            UM.MachineManager.setActiveMachineVariant(variantsModel.getItem(index).name);
                            if (typeof(model) !== "undefined" && !model.active) {
                                //Selecting a variant was canceled; undo menu selection
                                variantSelectionInstantiator.model.setProperty(index, "active", false);
                                var activeMachineVariantName = UM.MachineManager.activeMachineVariant;
                                var activeMachineVariantIndex = variantSelectionInstantiator.model.find("name", activeMachineVariantName);
                                variantSelectionInstantiator.model.setProperty(activeMachineVariantIndex, "active", true);
                            }
                        }
                    }
                    onObjectAdded: variantsSelectionMenu.insertItem(index, object)
                    onObjectRemoved: variantsSelectionMenu.removeItem(object)
                }

                ExclusiveGroup { id: variantSelectionMenuGroup; }
            }
        }
    }

    Rectangle {
        id: materialSelectionRow
        anchors.top: variantRow.bottom
        anchors.topMargin: UM.MachineManager.hasMaterials ? UM.Theme.getSize("default_margin").height : 0
        width: base.width
        height: UM.MachineManager.hasMaterials ? UM.Theme.getSize("sidebar_setup").height : 0
        visible: UM.MachineManager.hasMaterials

        Label{
            id: materialSelectionLabel
            text: catalog.i18nc("@label","Material:");
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width;
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width/100*45
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        ToolButton {
            id: materialSelection
            text: UM.MachineManager.activeMaterial
            width: parent.width/100*55
            height: UM.Theme.getSize("setting_control").height
            tooltip: UM.MachineManager.activeMaterial;
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            style: UM.Theme.styles.sidebar_header_button

            menu: Menu
            {
                id: materialSelectionMenu
                Instantiator
                {
                    id: materialSelectionInstantiator
                    model: UM.MachineMaterialsModel { id: machineMaterialsModel }
                    MenuItem
                    {
                        text: model.name;
                        checkable: true;
                        checked: model.active;
                        exclusiveGroup: materialSelectionMenuGroup;
                        onTriggered:
                        {
                            UM.MachineManager.setActiveMaterial(machineMaterialsModel.getItem(index).name);
                            if (typeof(model) !== "undefined" && !model.active) {
                                //Selecting a material was canceled; undo menu selection
                                materialSelectionInstantiator.model.setProperty(index, "active", false);
                                var activeMaterialName = UM.MachineManager.activeMaterial;
                                var activeMaterialIndex = materialSelectionInstantiator.model.find("name", activeMaterialName);
                                materialSelectionInstantiator.model.setProperty(activeMaterialIndex, "active", true);
                            }
                        }
                    }
                    onObjectAdded: materialSelectionMenu.insertItem(index, object)
                    onObjectRemoved: materialSelectionMenu.removeItem(object)
                }

                ExclusiveGroup { id: materialSelectionMenuGroup; }
            }
        }
    }
}
