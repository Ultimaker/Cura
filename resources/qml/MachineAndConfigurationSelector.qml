// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7

import UM 1.2 as UM
import Cura 1.0 as Cura
import "Menus"
import "Menus/ConfigurationMenu"

Rectangle
{
    color: UM.Theme.getColor("sidebar_lining_thin")

    implicitHeight: UM.Theme.getSize("sidebar_header").height
    implicitWidth: UM.Theme.getSize("sidebar").width

    property bool isNetworkPrinter: Cura.MachineManager.activeMachineNetworkKey != ""
    property bool printerConnected: Cura.MachineManager.printerConnected

    MachineSelection
    {
        id: machineSelection
        anchors
        {
            left: parent.left
            right: configSelection.left
            rightMargin: UM.Theme.getSize("sidebar_lining_thin").height / 2
            top: parent.top
            bottom: parent.bottom
        }
    }

    ConfigurationSelection
    {
        id: configSelection
        visible: isNetworkPrinter && printerConnected
        width: visible ? Math.round(parent.width * 0.15) : 0
        panelWidth: parent.width
        anchors
        {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
        }
    }
}