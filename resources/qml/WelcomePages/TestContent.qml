// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura

import "../MachineSettings"
import "../Widgets"


//
// This component contains the content for the "Welcome" page of the welcome on-boarding process.
//

Item
{
    id: base
    UM.I18nCatalog { id: catalog; name: "cura" }

    anchors.fill: parent
    anchors.margins: UM.Theme.getSize("default_margin").width

    property var extrudersModel: Cura.ExtrudersModel {}

    // If we create a CuraTabButton for "Printer" and use Repeater for extruders, for some reason, once the component
    // finishes it will automatically change "currentIndex = 1", and it is VERY difficult to change "currentIndex = 0"
    // after that. Using a model and a Repeater to create both "Printer" and extruder CuraTabButtons seem to solve this
    // problem.
    Connections
    {
        target: extrudersModel
        onItemsChanged: tabNameModel.update()
    }

    ListModel
    {
        id: tabNameModel

        Component.onCompleted: update()

        function update()
        {
            clear()
            append({ name: catalog.i18nc("@title:tab", "Printer") })
            for (var i = 0; i < extrudersModel.count; i++)
            {
                const m = extrudersModel.getItem(i)
                append({ name: m.name })
            }
        }
    }

    Rectangle
    {
        anchors.fill: parent
        border.color: tabBar.visible ? UM.Theme.getColor("lining") : "transparent"
        border.width: UM.Theme.getSize("default_lining").width
        radius: UM.Theme.getSize("default_radius").width

        UM.TabRow
        {
            id: tabBar
            width: parent.width

            Repeater
            {
                model: tabNameModel
                delegate: CuraTabButton
                {
                    text: model.name
                }
            }
        }

        StackLayout
        {
            id: tabStack
            anchors.top: tabBar.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom

            width: parent.width
            currentIndex: tabBar.currentIndex

            MachineSettingsPrinterTab
            {
                id: printerTab
            }

            Repeater
            {
                model: extrudersModel
                delegate: MachineSettingsExtruderTab
                {
                    id: discoverTab
                    extruderPosition: model.index
                    extruderStackId: model.id
                }
            }
        }
    }
}
