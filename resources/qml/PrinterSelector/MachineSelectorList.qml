// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.0 as Cura

ListView
{
    id: listView
    section.property: "isOnline"
    property real contentHeight: childrenRect.height

    ScrollBar.vertical: UM.ScrollBar
    {
        id: scrollBar
    }

    section.delegate: UM.Label
    {
        text: section == "true" ? catalog.i18nc("@label", "Connected printers") : catalog.i18nc("@label", "Other printers")
        height: UM.Theme.getSize("action_button").height
        width: parent.width - scrollBar.width
        leftPadding: UM.Theme.getSize("default_margin").width
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("text_medium")
    }

    delegate: MachineListButton
    {
        width: listView.width - scrollBar.width

        onClicked: function()
        {
            switch (model.componentType) {
                case "HIDE_BUTTON":
                    listView.model.setShowCloudPrinters(false);
                    break;
                case "SHOW_BUTTON":
                    listView.model.setShowCloudPrinters(true);
                    break;
                case "MACHINE":
                    toggleContent()
                    Cura.MachineManager.setActiveMachine(model.id)
                    break;
                default:
            }
        }
    }
}
