// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.4 as UM

// A row of buttons that control the view direction
Row
{
    id: viewOrientationControl

    spacing: UM.Theme.getSize("narrow_margin").width
    height: childrenRect.height
    width: childrenRect.width

    ViewOrientationButton
    {
        iconSource: UM.Theme.getIcon("view_3d")
        onClicked: UM.Controller.rotateView("3d", 0)
    }

    ViewOrientationButton
    {
        iconSource: UM.Theme.getIcon("view_front")
        onClicked: UM.Controller.rotateView("home", 0)
    }

    ViewOrientationButton
    {
        iconSource: UM.Theme.getIcon("view_top")
        onClicked: UM.Controller.rotateView("y", 90)
    }

    ViewOrientationButton
    {
        iconSource: UM.Theme.getIcon("view_left")
        onClicked: UM.Controller.rotateView("x", 90)
    }

    ViewOrientationButton
    {
        iconSource: UM.Theme.getIcon("view_right")
        onClicked: UM.Controller.rotateView("x", -90)
    }
}
