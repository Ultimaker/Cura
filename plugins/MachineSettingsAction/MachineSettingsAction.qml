// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "Welcome" page of the welcome on-boarding process.
//
Cura.MachineAction
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    anchors.fill: parent

    property var extrudersModel: Cura.ExtrudersModel {}

    // If we create a TabButton for "Printer" and use Repeater for extruders, for some reason, once the component
    // finishes it will automatically change "currentIndex = 1", and it is VERY difficult to change "currentIndex = 0"
    // after that. Using a model and a Repeater to create both "Printer" and extruder TabButtons seem to solve this
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

    Cura.RoundedRectangle
    {
        anchors
        {
            top: tabBar.bottom
            topMargin: -UM.Theme.getSize("default_lining").height
            bottom: parent.bottom
            left: parent.left
            right: parent.right
        }
        cornerSide: Cura.RoundedRectangle.Direction.Down
        border.color: UM.Theme.getColor("lining")
        border.width: UM.Theme.getSize("default_lining").width
        radius: UM.Theme.getSize("default_radius").width
        color: UM.Theme.getColor("main_background")
        StackLayout
        {
            id: tabStack
            anchors.fill: parent

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

    Label
    {
        id: machineNameLabel
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        text: Cura.MachineManager.activeMachine.name
        horizontalAlignment: Text.AlignHCenter
        font: UM.Theme.getFont("large_bold")
        renderType: Text.NativeRendering
    }

    UM.TabRow
    {
        id: tabBar
        anchors.top: machineNameLabel.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        Repeater
        {
            model: tabNameModel
            delegate: UM.TabRowButton
            {
                text: model.name
            }
        }
    }
}
