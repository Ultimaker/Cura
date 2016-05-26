// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: base;
    // Machine Setup
    property Action addMachineAction;
    property Action configureMachinesAction;
    UM.I18nCatalog { id: catalog; name:"cura"}
    property int totalHeightHeader: childrenRect.height
    property int currentExtruderIndex;

    Rectangle {
        id: sidebarTabRow
        width: base.width
        height: 0
        anchors.top: parent.top
        color: UM.Theme.getColor("sidebar_header_bar")
    }

    Rectangle {
        id: machineSelectionRow
        width: base.width
        height: UM.Theme.getSize("sidebar_setup").height
        anchors.top: sidebarTabRow.bottom
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
            text: Cura.MachineManager.activeMachineName;
            width: parent.width/100*55
            height: UM.Theme.getSize("setting_control").height
            tooltip: Cura.MachineManager.activeMachineName;
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            style: UM.Theme.styles.sidebar_header_button

            menu: Menu
            {
                id: machineSelectionMenu
                Instantiator
                {
                    model: UM.ContainerStacksModel
                    {
                        filter: {"type": "machine"}
                    }
                    MenuItem
                    {
                        text: model.name;
                        checkable: true;
                        checked: Cura.MachineManager.activeMachineId == model.id
                        exclusiveGroup: machineSelectionMenuGroup;
                        onTriggered: Cura.MachineManager.setActiveMachine(model.id);
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
        id: extruderSelection
        width: parent.width/100*55
        visible: machineExtruderCount.properties.value > 1
        height: visible ? UM.Theme.getSize("sidebar_header_mode_toggle").height : 0
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        anchors.top: machineSelectionRow.bottom
        anchors.topMargin: visible ? UM.Theme.getSize("default_margin").height : 0
        Component{
            id: wizardDelegate
            Button {
                height: extruderSelection.height
                anchors.left: parent.left
                anchors.leftMargin: model.index * (extruderSelection.width / machineExtruderCount.properties.value)
                anchors.verticalCenter: parent.verticalCenter
                width: parent.width / machineExtruderCount.properties.value
                text: model.text
                exclusiveGroup: extruderMenuGroup;
                checkable: true;
                checked: base.currentExtruderIndex == index
                onClicked: base.currentExtruderIndex = index

                style: ButtonStyle {
                    background: Rectangle {
                        border.width: UM.Theme.getSize("default_lining").width
                        border.color: control.checked ? UM.Theme.getColor("toggle_checked_border") :
                                          control.pressed ? UM.Theme.getColor("toggle_active_border") :
                                          control.hovered ? UM.Theme.getColor("toggle_hovered_border") : UM.Theme.getColor("toggle_unchecked_border")
                        color: control.checked ? UM.Theme.getColor("toggle_checked") :
                                   control.pressed ? UM.Theme.getColor("toggle_active") :
                                   control.hovered ? UM.Theme.getColor("toggle_hovered") : UM.Theme.getColor("toggle_unchecked")
                        Behavior on color { ColorAnimation { duration: 50; } }
                        Label {
                            anchors.centerIn: parent
                            color: control.checked ? UM.Theme.getColor("toggle_checked_text") :
                                       control.pressed ? UM.Theme.getColor("toggle_active_text") :
                                       control.hovered ? UM.Theme.getColor("toggle_hovered_text") : UM.Theme.getColor("toggle_unchecked_text")
                            font: UM.Theme.getFont("default")
                            text: control.text;
                        }
                    }
                    label: Item { }
                }
            }
        }
        ExclusiveGroup { id: extruderMenuGroup; }
        ListView{
            id: extrudersList
            property var index: 0
            model: extrudersListModel
            delegate: wizardDelegate
            anchors.top: parent.top
            anchors.left: parent.left
            width: parent.width
        }
    }

    ListModel
    {
        id: extrudersListModel
        Component.onCompleted: populateExtruderModel()
    }
    Connections
    {
        id: machineChange
        target: Cura.MachineManager
        onGlobalContainerChanged: populateExtruderModel()
    }

    function populateExtruderModel()
    {
        extrudersListModel.clear();
        for(var extruder = 0; extruder < machineExtruderCount.properties.value ; extruder++) {
            extrudersListModel.append({
                text: catalog.i18nc("@label", "Extruder %1").arg(extruder + 1)
            })
        }
    }

    Rectangle {
        id: variantRow
        anchors.top: extruderSelection.visible ? extruderSelection.bottom : machineSelectionRow.bottom
        anchors.topMargin: visible ? UM.Theme.getSize("default_margin").height : 0
        width: base.width
        height: visible ? UM.Theme.getSize("sidebar_setup").height : 0
        visible: Cura.MachineManager.hasVariants || Cura.MachineManager.hasMaterials

        Label{
            id: variantLabel
            text: (Cura.MachineManager.hasVariants && Cura.MachineManager.hasMaterials) ? catalog.i18nc("@label","Nozzle & Material:"):
                    Cura.MachineManager.hasVariants ? catalog.i18nc("@label","Nozzle:") : catalog.i18nc("@label","Material:");
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter
            width: parent.width/100*45
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        Rectangle
        {
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: parent.verticalCenter

            width: parent.width/100*55
            height: UM.Theme.getSize("setting_control").height

            ToolButton {
                id: variantSelection
                text: Cura.MachineManager.activeVariantName
                tooltip: Cura.MachineManager.activeVariantName;
                visible: Cura.MachineManager.hasVariants

                height: UM.Theme.getSize("setting_control").height
                width: materialSelection.visible ? (parent.width - UM.Theme.getSize("default_margin").width) / 2 : parent.width
                anchors.left: parent.left
                style: UM.Theme.styles.sidebar_header_button

                menu: Menu
                {
                    id: variantsSelectionMenu
                    Instantiator
                    {
                        id: variantSelectionInstantiator
                        model: UM.InstanceContainersModel
                        {
                            filter:
                            {
                                "type": "variant",
                                "definition": Cura.MachineManager.activeDefinitionId //Only show variants of this machine
                            }
                        }
                        MenuItem
                        {
                            text: model.name;
                            checkable: true;
                            checked: model.id == Cura.MachineManager.activeVariantId;
                            exclusiveGroup: variantSelectionMenuGroup;
                            onTriggered:
                            {
                                Cura.MachineManager.setActiveVariant(model.id);
                                /*if (typeof(model) !== "undefined" && !model.active) {
                                    //Selecting a variant was canceled; undo menu selection
                                    variantSelectionInstantiator.model.setProperty(index, "active", false);
                                    var activeMachineVariantName = UM.MachineManager.activeMachineVariant;
                                    var activeMachineVariantIndex = variantSelectionInstantiator.model.find("name", activeMachineVariantName);
                                    variantSelectionInstantiator.model.setProperty(activeMachineVariantIndex, "active", true);
                                }*/
                            }
                        }
                        onObjectAdded: variantsSelectionMenu.insertItem(index, object)
                        onObjectRemoved: variantsSelectionMenu.removeItem(object)
                    }

                    ExclusiveGroup { id: variantSelectionMenuGroup; }
                }
            }

            ToolButton {
                id: materialSelection
                text: Cura.MachineManager.activeMaterialName
                tooltip: Cura.MachineManager.activeMaterialName
                visible: Cura.MachineManager.hasMaterials

                height: UM.Theme.getSize("setting_control").height
                width: variantSelection.visible ? (parent.width - UM.Theme.getSize("default_margin").width) / 2 : parent.width
                anchors.right: parent.right
                style: UM.Theme.styles.sidebar_header_button

                menu: Menu
                {
                    id: materialSelectionMenu
                    Instantiator
                    {
                        id: materialSelectionInstantiator
                        model: UM.InstanceContainersModel
                        {
                            filter: { "type": "material", "definition": Cura.MachineManager.activeDefinitionId }
                        }
                        MenuItem
                        {
                            text: model.name;
                            checkable: true;
                            checked: model.id == Cura.MachineManager.activeMaterialId;
                            exclusiveGroup: materialSelectionMenuGroup;
                            onTriggered:
                            {
                                Cura.MachineManager.setActiveMaterial(model.id);
                                /*if (typeof(model) !== "undefined" && !model.active) {
                                    //Selecting a material was canceled; undo menu selection
                                    materialSelectionInstantiator.model.setProperty(index, "active", false);
                                    var activeMaterialName = Cura.MachineManager.activeMaterialName
                                    var activeMaterialIndex = materialSelectionInstantiator.model.find("name", activeMaterialName);
                                    materialSelectionInstantiator.model.setProperty(activeMaterialIndex, "active", true);
                                }*/
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

    UM.SettingPropertyProvider
    {
        id: machineExtruderCount

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_extruder_count"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }
}
