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

    onVisibleChanged:
    {
        if (visible)
        {
            tabBar.currentIndex = 0
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

            CuraTabButton
            {
                text: catalog.i18nc("@title:tab", "Printer")
            }

            Repeater
            {
                model: extrudersModel
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
                    extruderStackId: model.id
                }
            }
        }
    }
}
