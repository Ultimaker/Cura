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
    height: childrenRect.height + 2 * padding
    padding: UM.Theme.getSize("default_margin").width
    spacing: UM.Theme.getSize("default_margin").height

    Label {
        text: catalog.i18nc("@label:header configurations", "Available configurations")
        font: UM.Theme.getFont("large")
        width: parent.width - 2 * parent.padding
    }

    Item
    {
        id: container
        width: parent.width - 2 * parent.padding
        height: childrenRect.height

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
                    font: UM.Theme.getFont("default_bold")
                }

                ListView
                {
                    id: grid
                    anchors.top: printerTypeHeader.bottom
                    anchors.topMargin: UM.Theme.getSize("default_margin").height
                    width: container.width
                    height: childrenRect.height
                    model: outputDevice.printers
                    delegate: ConfigurationItem
                    {
                        height: parent.height
                        width: parent.width
                        printer: modelData
                        onConfigurationSelected:
                        {
                            print("SELECCIONANDO IMPRESORA", printer.name)
                            outputDevice.setActivePrinter(printer)
                        }
                    }
                }
            }
        }
    }
}