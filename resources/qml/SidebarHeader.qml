// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Column
{
    id: base;

    property int totalHeightHeader: childrenRect.height
    property int currentExtruderIndex;

    spacing: UM.Theme.getSize("default_margin").height

    signal showTooltip(Item item, point location, string text)
    signal hideTooltip()

    Row
    {
        id: machineSelectionRow
        height: UM.Theme.getSize("sidebar_setup").height

        anchors
        {
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
        }

        Label
        {
            id: machineSelectionLabel
            text: catalog.i18nc("@label:listbox", "Printer:");
            anchors.verticalCenter: parent.verticalCenter
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");

            width: parent.width * 0.45 - UM.Theme.getSize("default_margin").width
        }

        ToolButton
        {
            id: machineSelection
            text: Cura.MachineManager.activeMachineName;

            height: UM.Theme.getSize("setting_control").height
            tooltip: Cura.MachineManager.activeMachineName;
            anchors.verticalCenter: parent.verticalCenter
            style: UM.Theme.styles.sidebar_header_button

            width: parent.width * 0.55 + UM.Theme.getSize("default_margin").width

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

                MenuItem { action: Cura.Actions.addMachine; }
                MenuItem { action: Cura.Actions.configureMachines; }
            }
        }
    }

    ListView
    {
        id: extrudersList
        property var index: 0

        visible: machineExtruderCount.properties.value > 1
        height: UM.Theme.getSize("sidebar_header_mode_toggle").height

        boundsBehavior: Flickable.StopAtBounds

        anchors
        {
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
        }

        ExclusiveGroup { id: extruderMenuGroup; }

        orientation: ListView.Horizontal

        model: Cura.ExtrudersModel { id: extrudersModel; addGlobal: true }

        delegate: Button
        {
            height: ListView.view.height
            width: ListView.view.width / extrudersModel.rowCount()

            text: model.name
            exclusiveGroup: extruderMenuGroup;
            checkable: true;
            checked: base.currentExtruderIndex == index

            onClicked:
            {
                focus = true; //Changing focus applies the currently-being-typed values so it can change the displayed setting values.
                base.currentExtruderIndex = index;
                ExtruderManager.setActiveExtruderIndex(index);
            }

            style: ButtonStyle
            {
                background: Rectangle
                {
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: control.checked ? UM.Theme.getColor("toggle_checked_border") :
                                        control.pressed ? UM.Theme.getColor("toggle_active_border") :
                                        control.hovered ? UM.Theme.getColor("toggle_hovered_border") : UM.Theme.getColor("toggle_unchecked_border")
                    color: control.checked ? UM.Theme.getColor("toggle_checked") :
                                control.pressed ? UM.Theme.getColor("toggle_active") :
                                control.hovered ? UM.Theme.getColor("toggle_hovered") : UM.Theme.getColor("toggle_unchecked")
                    Behavior on color { ColorAnimation { duration: 50; } }

                    Label
                    {
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

    Row
    {
        id: variantRow

        height: UM.Theme.getSize("sidebar_setup").height
        visible: Cura.MachineManager.hasVariants || Cura.MachineManager.hasMaterials

        anchors
        {
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
        }

        Label
        {
            id: variantLabel
            text: (Cura.MachineManager.hasVariants && Cura.MachineManager.hasMaterials) ? catalog.i18nc("@label","Nozzle & Material:"):
                    Cura.MachineManager.hasVariants ? catalog.i18nc("@label","Nozzle:") : catalog.i18nc("@label","Material:");

            anchors.verticalCenter: parent.verticalCenter
            width: parent.width * 0.45 - UM.Theme.getSize("default_margin").width
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        Rectangle
        {
            anchors.verticalCenter: parent.verticalCenter

            width: parent.width * 0.55 + UM.Theme.getSize("default_margin").width
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
                            text: model.name;
                            checkable: true;
                            checked: model.id == Cura.MachineManager.activeMaterialId;
                            exclusiveGroup: materialSelectionMenuGroup;
                            onTriggered:
                            {
                                Cura.MachineManager.setActiveMaterial(model.id);
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

    Row
    {
        id: globalProfileRow
        height: UM.Theme.getSize("sidebar_setup").height

        anchors
        {
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
        }


        Label
        {
            id: globalProfileLabel
            text: catalog.i18nc("@label","Profile:");
            width: parent.width * 0.45 - UM.Theme.getSize("default_margin").width
            font: UM.Theme.getFont("default");
            color: UM.Theme.getColor("text");
        }

        ToolButton
        {
            id: globalProfileSelection
            text: Cura.MachineManager.activeQualityName
            width: parent.width * 0.55 + UM.Theme.getSize("default_margin").width
            height: UM.Theme.getSize("setting_control").height
            tooltip: Cura.MachineManager.activeQualityName
            style: UM.Theme.styles.sidebar_header_button

            menu: Menu
            {
                id: profileSelectionMenu
                Instantiator
                {
                    id: profileSelectionInstantiator
                    model: UM.InstanceContainersModel
                    {
                        filter:
                        {
                            var result = { "type": "quality" };
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
                    property int separatorIndex: -1

                    Loader {
                        property QtObject model_data: model
                        property int model_index: index
                        sourceComponent: menuItemDelegate
                    }
                    onObjectAdded:
                    {
                        //Insert a separator between readonly and custom profiles
                        if(separatorIndex < 0 && index > 0)
                        {
                            if(model.getItem(index-1).readOnly != model.getItem(index).readOnly)
                            {
                                profileSelectionMenu.insertSeparator(index);
                                separatorIndex = index;
                            }
                        }
                        //Because of the separator, custom profiles move one index lower
                        profileSelectionMenu.insertItem((model.getItem(index).readOnly) ? index : index + 1, object.item);
                    }
                    onObjectRemoved:
                    {
                        //When adding a profile, the menu is rebuilt by removing all items.
                        //If a separator was added, we need to remove that too.
                        if(separatorIndex >= 0)
                        {
                            profileSelectionMenu.removeItem(profileSelectionMenu.items[separatorIndex])
                            separatorIndex = -1;
                        }
                        profileSelectionMenu.removeItem(object.item);
                    }
                }
                ExclusiveGroup { id: profileSelectionMenuGroup; }

                Component
                {
                    id: menuItemDelegate
                    MenuItem
                    {
                        id: item
                        text: model_data ? model_data.name : ""
                        checkable: true
                        checked: model_data != null ? Cura.MachineManager.activeQualityId == model_data.id : false
                        exclusiveGroup: profileSelectionMenuGroup;
                        onTriggered: Cura.MachineManager.setActiveQuality(model_data.id)
                    }
                }

                MenuSeparator { }
                MenuItem { action: Cura.Actions.addProfile }
                MenuItem { action: Cura.Actions.updateProfile }
                MenuItem { action: Cura.Actions.resetProfile }
                MenuSeparator { }
                MenuItem { action: Cura.Actions.manageProfiles }
            }

            UM.SimpleButton
            {
                id: customisedSettings

                visible: Cura.MachineManager.hasUserSettings
                height: parent.height * 0.6
                width: parent.height * 0.6

                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("setting_preferences_button_margin").width - UM.Theme.getSize("default_margin").width

                color: hovered ? UM.Theme.getColor("setting_control_button_hover") : UM.Theme.getColor("setting_control_button");
                iconSource: UM.Theme.getIcon("star");

                onClicked: Cura.Actions.manageProfiles.trigger()
                onEntered:
                {
                    var content = catalog.i18nc("@tooltip","Some setting values are different from the values stored in the profile.\n\nClick to open the profile manager.")
                    base.showTooltip(globalProfileRow, Qt.point(0, globalProfileRow.height / 2),  content)
                }
                onExited: base.hideTooltip()
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

    UM.I18nCatalog { id: catalog; name:"cura" }
}
