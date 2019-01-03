// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura


// This element hold all the elements needed for the user to trigger the slicing process, and later
// to get information about the printing times, material consumption and the output process (such as
// saving to a file, printing over network, ...
Rectangle
{
    id: actionPanelWidget

    width: UM.Theme.getSize("action_panel_widget").width
    height: childrenRect.height + 2 * UM.Theme.getSize("thick_margin").height

    color: UM.Theme.getColor("main_background")
    border.width: UM.Theme.getSize("default_lining").width
    border.color: UM.Theme.getColor("lining")
    radius: UM.Theme.getSize("default_radius").width
    z: 10

    property bool outputAvailable: UM.Backend.state == UM.Backend.Done || UM.Backend.state == UM.Backend.Disabled

    Loader
    {
        id: loader
        anchors
        {
            top: parent.top
            topMargin: UM.Theme.getSize("thick_margin").height
            left: parent.left
            leftMargin: UM.Theme.getSize("thick_margin").width
            right: parent.right
            rightMargin: UM.Theme.getSize("thick_margin").width
        }
        sourceComponent: outputAvailable ? outputProcessWidget : sliceProcessWidget
    }

    Component
    {
        id: sliceProcessWidget
        SliceProcessWidget { }
    }

    Component
    {
        id: outputProcessWidget
        OutputProcessWidget { }
    }
}