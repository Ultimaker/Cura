// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.0 as Cura

ListView
{
    id: listView
    model: Cura.MachineListModel {}
    section.property: "isOnline"
    property real contentHeight: childrenRect.height

    ScrollBar.vertical: UM.ScrollBar
    {
        id: scrollBar
    }

    section.delegate: Item
    {
        width: parent.width - scrollBar.width
        height: childrenRect.height

        UM.Label
        {
            visible: section == "true"
            text: catalog.i18nc("@label", "Connected printers")
            height: UM.Theme.getSize("action_button").height
            leftPadding: UM.Theme.getSize("default_margin").width
            font: UM.Theme.getFont("medium")
            color: UM.Theme.getColor("text_medium")
        }

        Column
        {
            visible: section != "true"
            height: childrenRect.height

            Cura.TertiaryButton
            {
                text: listView.model.showCloudPrinters ? catalog.i18nc("@label", "Hide all connected printers") : catalog.i18nc("@label", "Show all connected printers")
                onClicked: listView.model.setShowCloudPrinters(!listView.model.showCloudPrinters)
                iconSource: listView.model.showCloudPrinters ? UM.Theme.getIcon("ChevronSingleUp") : UM.Theme.getIcon("ChevronSingleDown")
            }

            UM.Label
            {
                text: catalog.i18nc("@label", "Other printers")
                height: UM.Theme.getSize("action_button").height
                leftPadding: UM.Theme.getSize("default_margin").width
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text_medium")
            }
        }
    }

    delegate: MachineListButton
    {
        text: model.name ? model.name : ""
        width: listView.width - scrollBar.width

        onClicked:
        {
            toggleContent()
            Cura.MachineManager.setActiveMachine(model.id)
        }
    }
}
