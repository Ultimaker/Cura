// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.15

import UM 1.4 as UM
import Cura 1.1 as Cura

Item
{
    id: applicationSwitcherWidget
    width: Math.round(0.5 * UM.Theme.getSize("main_window_header").height)
    height: width

    Button
    {
        id: applicationSwitcherButton

        anchors.fill: parent

        background: Item
        {
            Rectangle
            {
                anchors.fill: parent
                radius: UM.Theme.getSize("action_button_radius").width
                color: UM.Theme.getColor("primary_text")
                opacity: applicationSwitcherButton.hovered ? 0.2 : 0
                Behavior on opacity { NumberAnimation { duration: 100; } }
            }

            UM.RecolorImage
            {
                anchors.fill: parent
                color: UM.Theme.getColor("primary_text")

                source: UM.Theme.getIcon("BlockGrid")
            }
        }

        onClicked:
        {
            if (applicationSwitcherPopup.opened)
            {
                applicationSwitcherPopup.close()
            } else {
                applicationSwitcherPopup.open()
            }
        }
    }
    ApplicationSwitcherPopup
    {
        id: applicationSwitcherPopup
        y: parent.height + UM.Theme.getSize("default_arrow").height

        // Move the x position by the default margin so that the arrow isn't drawn exactly on the corner
        x: parent.width - width + UM.Theme.getSize("default_margin").width
    }
}