// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.0 as Cura

ListView
{
    id: listView
    section.property: "category"
    property real contentHeight: childrenRect.height
    property var onSelectPrinter

    ScrollBar.vertical: UM.ScrollBar
    {
        id: scrollBar
    }

    section.delegate: UM.Label
    {
        text: {
            switch (section)
            {
                case "connected":
                    return catalog.i18nc("@label", "Connected printers");
                case "other":
                    return catalog.i18nc("@label", "Other printers");
                default:
                    return catalog.i18nc("@label", "Other printers");
            }
        }
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
                    if (typeof onSelectPrinter === "function") onSelectPrinter(model);
                    break;
                default:
            }
        }
    }
}
