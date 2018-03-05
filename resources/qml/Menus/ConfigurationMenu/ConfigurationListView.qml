// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Column
{
    id: base
    property var outputDevice: Cura.MachineManager.printerOutputDevices[0]
    height: childrenRect.height + 2 * padding
    padding: UM.Theme.getSize("default_margin").width
    spacing: Math.round(UM.Theme.getSize("default_margin").height / 2)

    Label {
        text: catalog.i18nc("@label:header configurations", "Available configurations")
        font: UM.Theme.getFont("large")
        width: parent.width - 2 * parent.padding
    }

    ScrollView {
        id: container
        width: parent.width - 2 * parent.padding
        height: 500 //childrenRect.height

        style: UM.Theme.styles.scrollview

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

                Connections {
                    target: outputDevice
                    onUniqueConfigurationsChanged: {
                        // FIXME For now the model should be removed and then created again, otherwise changes in the printer don't automatically update the UI
                        configurationList.model = null
                        configurationList.model = outputDevice.uniqueConfigurations
                    }
                }

                ListView
                {
                    id: configurationList
                    anchors.top: printerTypeHeader.bottom
                    anchors.topMargin: UM.Theme.getSize("default_margin").height
                    width: container.width
                    height: childrenRect.height
                    model: outputDevice.uniqueConfigurations
                    delegate: ConfigurationItem
                    {
                        width: parent.width
                        configuration: modelData
                        onConfigurationSelected:
                        {
                            print("SELECCIONANDO CONFIGURACION", JSON.stringify(configuration))
                        }
                    }
                }
            }
        }
    }
}