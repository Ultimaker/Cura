// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.
import QtQuick 2.2
import QtQuick.Controls 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Instantiator {

    model: UM.ContainerStacksModel {
        filter: {"type": "machine", "um_cloud_cluster_id": "*", "hidden": "False"}
    }

    MenuItem {
        // iconSource: UM.Theme.getIcon("printer_single") TODO: use cloud icon here
        text: model.name
        checkable: true
        checked: true // cloud printers are only listed if they are actually online
        exclusiveGroup: group;
        onTriggered: Cura.MachineManager.setActiveMachine(model.id);
    }

    onObjectAdded: menu.insertItem(index, object)
    onObjectRemoved: menu.removeItem(object)
}
