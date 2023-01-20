// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10

import UM 1.5 as UM
import Cura 1.0 as Cura

Item
{
    id: base
    property string label
    height: childrenRect.height

    Rectangle
    {
        color: UM.Theme.getColor("setting_category")
        width: base.width
        height: UM.Theme.getSize("section").height

        UM.Label
        {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            text: label
        }
    }
}
