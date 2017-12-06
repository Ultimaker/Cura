// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Menu
{
    title: catalog.i18nc("@title:menu menubar:toplevel", "&View");
    id: menu
    enabled: !PrintInformation.preSliced
    Instantiator
    {
        model: UM.ViewModel { }
        MenuItem
        {
            text: model.name;
            checkable: true;
            checked: model.active;
            exclusiveGroup: group;
            onTriggered: UM.Controller.setActiveView(model.id);
        }
        onObjectAdded: menu.insertItem(index, object)
        onObjectRemoved: menu.removeItem(object)
    }
    ExclusiveGroup { id: group; }

    MenuSeparator {}
    MenuItem { action: Cura.Actions.homeCamera; }
}
