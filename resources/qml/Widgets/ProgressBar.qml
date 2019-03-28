// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.0 as Cura

//
// Cura-style progress bar, with a grey background and a blue indication bar.
//
ProgressBar
{
    id: progressBar
    width: parent.width
    height: UM.Theme.getSize("progressbar").height

    background: Rectangle
    {
        anchors.fill: parent
        radius: UM.Theme.getSize("progressbar_radius").width
        color: UM.Theme.getColor("progressbar_background")
    }

    contentItem: Item
    {
        anchors.fill: parent

        Rectangle
        {
            width: progressBar.visualPosition * parent.width
            height: parent.height
            radius: UM.Theme.getSize("progressbar_radius").width
            color: UM.Theme.getColor("progressbar_control")
        }
    }
}
