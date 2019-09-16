// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: base
    property var outputDevice: null
    height: childrenRect.height

    function forceModelUpdate()
    {
        // FIXME For now the model has to be removed and then created again, otherwise changes in the printer don't automatically update the UI
        configurationList.model = []
        if (outputDevice)
        {
            configurationList.model = outputDevice.uniqueConfigurations
        }
    }

    // This component will appear when there are no configurations (e.g. when losing connection or when they are being loaded)
    Item
    {
        width: parent.width
        visible: configurationList.model.length == 0
        height: label.height + UM.Theme.getSize("wide_margin").height
        anchors.top: parent.top
        anchors.topMargin: UM.Theme.getSize("default_margin").height

        UM.RecolorImage
        {
            id: icon

            anchors.left: parent.left
            anchors.verticalCenter: label.verticalCenter

            source: UM.Theme.getIcon("warning")
            color: UM.Theme.getColor("warning")
            width: UM.Theme.getSize("section_icon").width
            height: width
        }

        Label
        {
            id: label
            anchors.left: icon.right
            anchors.right: parent.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            // There are two cases that we want to diferenciate, one is when Cura is loading the configurations and the
            // other when the connection was lost
            text: Cura.MachineManager.printerConnected ?
                    catalog.i18nc("@label", "Loading available configurations from the printer...") :
                    catalog.i18nc("@label", "The configurations are not available because the printer is disconnected.")
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
            wrapMode: Text.WordWrap
        }
    }

    Cura.ScrollView
    {
        id: container
        width: parent.width
        readonly property int maximumHeight: 350 * screenScaleFactor
        height: Math.round(Math.min(configurationList.height, maximumHeight))
        contentHeight: configurationList.height
        clip: true

        ButtonGroup
        {
            buttons: configurationList.children
        }

        ListView
        {
            id: configurationList
            spacing: UM.Theme.getSize("narrow_margin").height
            width: container.width - ((height > container.maximumHeight) ? container.ScrollBar.vertical.background.width : 0) //Make room for scroll bar if there is any.
            height: childrenRect.height
            interactive: false  // let the ScrollView process scroll events.

            section.property: "modelData.printerType"
            section.criteria: ViewSection.FullString
            section.delegate: Item
            {
                height: printerTypeLabel.height + UM.Theme.getSize("wide_margin").height //Causes a default margin above the label and a default margin below the label.
                Cura.PrinterTypeLabel
                {
                    id: printerTypeLabel
                    text: Cura.MachineManager.getAbbreviatedMachineName(section)
                    anchors.verticalCenter: parent.verticalCenter //One default margin above and one below.
                }
            }

            model: (outputDevice != null) ? outputDevice.uniqueConfigurations : []

            delegate: ConfigurationItem
            {
                width: parent.width
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
