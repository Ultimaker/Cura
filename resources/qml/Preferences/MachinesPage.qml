// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Window 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura


UM.ManagementPage
{
    id: base
    Item { enabled: false; UM.I18nCatalog { id: catalog; name: "cura"} }

    title: catalog.i18nc("@title:tab", "Printers")
    detailsPlaneCaption: base.currentItem && base.currentItem.name ? base.currentItem.name : ""

    model: Cura.GlobalStacksModel { filterAbstractMachines: false }

    sectionRole: "discoverySource"

    activeId: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.id: ""
    activeIndex: activeMachineIndex()
    onHamburgeButtonClicked: {
        const hamburerButtonHeight = hamburger_button.height;
        menu.popup(hamburger_button, -menu.width + hamburger_button.width / 2, hamburger_button.height);
        // for some reason the height of the hamburger changes when opening the popup
        // reset height to initial heigt
        hamburger_button.height = hamburerButtonHeight;
    }
    hamburgerButtonVisible: Cura.MachineManager.activeMachine !== null

    function activeMachineIndex()
    {
        for(var i = 0; i < model.count; i++)
        {
            if (model.getItem(i).id == base.activeId)
            {
                return i;
            }
        }
        return -1;
    }

    buttons: [
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@action:button", "Add New")
            onClicked: Cura.Actions.addMachine.trigger()
        }
    ]

    Flow
    {
        visible: base.currentItem != null && currentItem && currentItem.id == Cura.MachineManager.activeMachine.id
        anchors.fill: parent
        spacing: UM.Theme.getSize("default_margin").height


        Repeater
        {
            id: machineActionRepeater
            model: base.currentItem ? CuraApplication.getSupportedActionMachineList(base.currentItem.id) : null

            Item
            {
                width: Math.round(childrenRect.width + 2 * screenScaleFactor)
                height: childrenRect.height
                visible: machineActionRepeater.model[index].visible
                Cura.SecondaryButton
                {
                    text: machineActionRepeater.model[index].label
                    onClicked:
                    {
                        var currentItem = machineActionRepeater.model[index]
                        if (currentItem.shouldOpenAsDialog) {
                            actionDialog.loader.manager = currentItem
                            actionDialog.loader.source = currentItem.qmlPath
                            actionDialog.title = currentItem.label
                            actionDialog.show()
                        } else {
                            currentItem.execute()
                        }
                    }
                }
            }
        }
    }

    Item
    {
        UM.Dialog
        {
            id: actionDialog
            minimumWidth: UM.Theme.getSize("modal_window_minimum").width
            minimumHeight: UM.Theme.getSize("modal_window_minimum").height
            maximumWidth: minimumWidth * 3
            maximumHeight: minimumHeight * 3
            backgroundColor: UM.Theme.getColor("main_background")
            onVisibleChanged:
            {
                if(!visible)
                {
                    actionDialog.loader.item.focus = true
                }
            }
        }

        UM.ConfirmRemoveDialog
        {
            id: confirmDialog
            object: base.currentItem && base.currentItem.name ? base.currentItem.name : ""
            text: base.currentItem ? base.currentItem.removalWarning : ""

            onAccepted:
            {
                Cura.MachineManager.removeMachine(base.currentItem.id)
                if(!base.currentItem)
                {
                    objectList.currentIndex = activeMachineIndex()
                }
                //Force updating currentItem and the details panel
                objectList.onCurrentIndexChanged()
            }
        }

        Cura.RenameDialog
        {
            id: renameDialog
            object: base.currentItem && base.currentItem.name ? base.currentItem.name : ""
            property var machine_name_validator: Cura.MachineNameValidator { }
            validName: renameDialog.newName.match(renameDialog.machine_name_validator.machineNameRegex) != null
            onAccepted:
            {
                Cura.MachineManager.renameMachine(base.currentItem.id, newName.trim())
                //Force updating currentItem and the details panel
                objectList.onCurrentIndexChanged()
            }
        }

        Cura.Menu
        {
            id: menu
            Cura.MenuItem
            {
                text: catalog.i18nc("@action:button", "Activate")
                enabled: base.currentItem != null && base.currentItem.id != Cura.MachineManager.activeMachine.id
                onTriggered: Cura.MachineManager.setActiveMachine(base.currentItem.id)
            }
            Cura.MenuItem
            {
                text: catalog.i18nc("@action:button", "Remove")
                enabled: base.currentItem != null && model.count > 1
                onTriggered: confirmDialog.open()
            }
            Cura.MenuItem
            {
                text: catalog.i18nc("@action:button", "Rename")
                enabled: base.currentItem != null && base.currentItem.metadata.group_name == null
                onTriggered:  renameDialog.open()
            }
       }

        Connections
        {
            target: Cura.MachineManager
            function onGlobalContainerChanged()
            {
                objectList.currentIndex = activeMachineIndex()
                objectList.onCurrentIndexChanged()
            }
        }
    }
}
