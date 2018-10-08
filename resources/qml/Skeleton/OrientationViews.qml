// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1

import UM 1.4 as UM

// View orientation Item
Row
{
    id: viewOrientationControl

    spacing: 2 * screenScaleFactor

    // #1 3d view
    Button
    {
        iconSource: UM.Theme.getIcon("view_3d")
        style: UM.Theme.styles.small_tool_button
        onClicked:UM.Controller.rotateView("3d", 0)
    }

    // #2 Front view
    Button
    {
        iconSource: UM.Theme.getIcon("view_front")
        style: UM.Theme.styles.small_tool_button
        onClicked: UM.Controller.rotateView("home", 0)
    }

    // #3 Top view
    Button
    {
        iconSource: UM.Theme.getIcon("view_top")
        style: UM.Theme.styles.small_tool_button
        onClicked: UM.Controller.rotateView("y", 90)
    }

    // #4 Left view
    Button
    {
        iconSource: UM.Theme.getIcon("view_left")
        style: UM.Theme.styles.small_tool_button
        onClicked: UM.Controller.rotateView("x", 90)
    }

    // #5 Right view
    Button
    {
        iconSource: UM.Theme.getIcon("view_right")
        style: UM.Theme.styles.small_tool_button
        onClicked: UM.Controller.rotateView("x", -90)
    }
}
