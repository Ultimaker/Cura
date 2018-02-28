// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

Column
{
    id: base
    property var outputDevice: Cura.MachineManager.printerOutputDevices[0]

    Rectangle
    {
        id: header
        color: "red"
        height: 25
        width: parent.width
    }

    Repeater {
        height: childrenRect.height
        model: outputDevice != null ? outputDevice.connectedPrintersTypeCount : null
        delegate: Rectangle
        {
            height: childrenRect.height
            Label
            {
                id: printerTypeHeader
                text: modelData.machine_type
            }

            GridView
            {
                id: grid
                anchors.top: printerTypeHeader.bottom
                anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
                width: base.width
                cellWidth: Math.round(base.width / 2)
                cellHeight: 100 * screenScaleFactor
                model: outputDevice.printers
                delegate: ConfigurationItem
                {
                    height: grid.cellHeight
                    width: grid.cellWidth
                    printer: modelData
                    onConfigurationSelected:
                    {
                        outputDevice.setActivePrinter(printer)
                    }
                }
            }
        }
    }
}