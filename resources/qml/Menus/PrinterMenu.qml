// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.4

import UM 1.6 as UM
import Cura 1.0 as Cura

Menu
{
    id: menu

    UM.MenuItem
    {
        id: networkEnabledPrinterItem
        text: catalog.i18nc("@label:category menu label", "Network enabled printers")
        enabled: false
        visible: networKPrinterInstantiator.count > 0
    }

    Instantiator
    {
        id: networKPrinterInstantiator
        model: Cura.GlobalStacksModel {filterOnlineOnly: true}
        UM.MenuItem
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
            onTriggered:
             {
             print(typeof(model.id))
                Cura.MachineManager.someFunction("YAY")
                Cura.MachineManager.setActiveMachine(model.id)
            }
        }
        onObjectAdded: menu.insertItem(2, object)
        onObjectRemoved: menu.removeItem(object)
    }

    MenuSeparator
    {
        visible: networKPrinterInstantiator.count > 0
    }

    UM.MenuItem
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

        UM.MenuItem
        {
            text: model.name
            checkable: true
            checked: Cura.MachineManager.activeMachine !== null ? Cura.MachineManager.activeMachine.id == model.id: false
            visible: !model.hasRemoteConnection
            height: visible ? implicitHeight: 0
            onTriggered: Cura.MachineManager.setActiveMachine(model.id)
        }
        // A bit hackish, but we have 2 items at the end, put them before that
        onObjectAdded: menu.insertItem(menu.count - 2, object)
        onObjectRemoved: menu.removeItem(object)
    }

    MenuSeparator
    {
        visible: localPrinterInstantiator.count > 0
    }

    UM.MenuItem { action: Cura.Actions.addMachine }
    UM.MenuItem { action: Cura.Actions.configureMachines }
}
