// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.4

import UM 1.6 as UM
import Cura 1.0 as Cura

Cura.Menu
{
    id: menu
    title: catalog.i18nc("@title:menu menubar:settings", "&Printer")
    Cura.MenuItem
    {
        id: networkEnabledPrinterItem
        text: catalog.i18nc("@label:category menu label", "Network enabled printers")
        enabled: false
        visible: networKPrinterInstantiator.count > 0
    }

    Instantiator
    {
        id: networKPrinterInstantiator
        model: Cura.GlobalStacksModel {filterOnlineOnly: true }
        Cura.MenuItem
        {
            property string connectGroupName:
            {
                if("group_name" in model.metadata)
                {
                    return model.metadata["group_name"]
                }
                return ""
            }
            text: connectGroupName
            checkable: true
            checked: Cura.MachineManager.activeMachineNetworkGroupName == connectGroupName
            onTriggered: Cura.MachineManager.setActiveMachine(model.id)
        }
        onObjectAdded: function(index, object) { menu.insertItem(2, object)}
        onObjectRemoved: function(index, object) {  menu.removeItem(object)}
    }

    Cura.MenuSeparator { visible: networKPrinterInstantiator.count > 0 }

    Cura.MenuItem
    {
        id: localPrinterMenu
        text: catalog.i18nc("@label:category menu label", "Local printers")
        enabled: false
        visible: localPrinterInstantiator.count > 0
    }

    Instantiator
    {
        id: localPrinterInstantiator
        model: Cura.GlobalStacksModel {}

        Cura.MenuItem
        {
            text: model.name
            checkable: true
            checked: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.id == model.id: false
            visible: !model.hasRemoteConnection
            onTriggered: Cura.MachineManager.setActiveMachine(model.id)
        }
        // A bit hackish, but we have 2 items at the end, put them before that
        onObjectAdded: function(index, object) { menu.insertItem(menu.count - 2, object) }
        onObjectRemoved: function(index, object) {  menu.removeItem(object) }
    }

    Cura.MenuSeparator { visible: localPrinterInstantiator.count > 0 }

    Cura.MenuItem { action: Cura.Actions.addMachine }
    Cura.MenuItem { action: Cura.Actions.configureMachines }
}
