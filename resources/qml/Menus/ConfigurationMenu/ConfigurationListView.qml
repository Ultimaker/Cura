// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Column
{
    id: base
    property var outputDevice: null
    height: childrenRect.height + 2 * padding
    spacing: Math.round(UM.Theme.getSize("default_margin").height / 2)

    function forceModelUpdate()
    {
        // FIXME For now the model should be removed and then created again, otherwise changes in the printer don't automatically update the UI
        configurationList.model = []
        if(outputDevice)
        {
            configurationList.model = outputDevice.uniqueConfigurations
        }
    }

    ScrollView
    {
        id: container
        width: parent.width - parent.padding
        height: Math.min(configurationList.contentHeight, 350 * screenScaleFactor)

        ButtonGroup
        {
            buttons: configurationList.children
        }

        ListView
        {
            id: configurationList
            spacing: Math.round(UM.Theme.getSize("default_margin").height / 2)
            width: container.width
            contentHeight: childrenRect.height

            section.property: "modelData.printerType"
            section.criteria: ViewSection.FullString
            section.delegate: Item
            {
                height: printerTypeLabelBox.height + UM.Theme.getSize("default_margin").height
                Rectangle
                {
                    id: printerTypeLabelBox
                    color: UM.Theme.getColor("text_detail")
                    width: childrenRect.width
                    height: childrenRect.height

                    Label
                    {
                        text: section
                        font: UM.Theme.getFont("small")
                        color: UM.Theme.getColor("text")
                        padding: UM.Theme.getSize("narrow_margin").width
                    }
                }
            }

            model: (outputDevice != null) ? outputDevice.uniqueConfigurations : []

            delegate: ConfigurationItem
            {
                width: parent.width - UM.Theme.getSize("default_margin").width
                configuration: modelData
            }
        }
    }

    Connections
    {
        target: outputDevice
        onUniqueConfigurationsChanged:
        {
            forceModelUpdate()
        }
    }

    Connections
    {
        target: Cura.MachineManager
        onOutputDevicesChanged:
        {
            forceModelUpdate()
        }
    }
}