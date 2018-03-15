// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Instantiator {
    model: UM.ContainerStacksModel {
        filter: {"type": "machine", "um_network_key": "*", "hidden": "False"}
    }
    MenuItem {
        // TODO: Use printer_group icon when it's a cluster. Not use it for now since it doesn't look as expected
//        iconSource: UM.Theme.getIcon("printer_single")
        text: model.metadata["connect_group_name"]
        checkable: true;
        checked: Cura.MachineManager.activeMachineNetworkGroupName == model.metadata["connect_group_name"]
        exclusiveGroup: group;
        onTriggered: Cura.MachineManager.setActiveMachine(model.id);
    }
    onObjectAdded: menu.insertItem(index, object)
    onObjectRemoved: menu.removeItem(object)
}
