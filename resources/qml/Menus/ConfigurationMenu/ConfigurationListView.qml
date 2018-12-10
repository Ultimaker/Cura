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
    property var outputDevice: null
    property var computedHeight: container.height + configurationListHeading.height + 3 * padding
    height: childrenRect.height + 2 * padding
    padding: UM.Theme.getSize("default_margin").width
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

    Label
    {
        id: configurationListHeading
        text: catalog.i18nc("@label:header configurations", "Available configurations")
        font: UM.Theme.getFont("large")
        width: parent.width - 2 * parent.padding
        color: UM.Theme.getColor("configuration_item_text")
    }

    Component
    {
        id: sectionHeading
        Rectangle
        {
            height: childrenRect.height + UM.Theme.getSize("default_margin").height
            Label
            {
                text: section
                font: UM.Theme.getFont("default_bold")
                color: UM.Theme.getColor("configuration_item_text")
            }
        }
    }

    ScrollView
    {
        id: container
        width: parent.width
        readonly property int maximumHeight: 350 * screenScaleFactor
        height: Math.round(Math.min(configurationList.height, maximumHeight))
        contentHeight: configurationList.height
        clip: true

        ScrollBar.vertical.policy: (configurationList.height > maximumHeight) ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff //The AsNeeded policy also hides it when the cursor is away, and we don't want that.
        ScrollBar.vertical.background: Rectangle
        {
            implicitWidth: UM.Theme.getSize("scrollbar").width
            radius: width / 2
            color: UM.Theme.getColor("scrollbar_background")
        }
        ScrollBar.vertical.contentItem: Rectangle
        {
            implicitWidth: UM.Theme.getSize("scrollbar").width
            radius: width / 2
            color: UM.Theme.getColor(parent.pressed ? "scrollbar_handle_down" : parent.hovered ? "scrollbar_handle_hover" : "scrollbar_handle")
        }

        style: UM.Theme.styles.scrollview
        __wheelAreaScrollSpeed: 75 // Scroll three lines in one scroll event

        ListView
        {
            id: configurationList
            spacing: Math.round(UM.Theme.getSize("default_margin").height / 2)
            width: container.width - ((height > container.maximumHeight) ? container.ScrollBar.vertical.background.width : 0) //Make room for scroll bar if there is any.
            contentHeight: childrenRect.height
            height: childrenRect.height

            section.property: "modelData.printerType"
            section.criteria: ViewSection.FullString
            section.delegate: Item
            {
                height: printerTypeLabel.height + UM.Theme.getSize("default_margin").height * 2 //Causes a default margin above the label and a default margin below the label.
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
                width: parent.width - UM.Theme.getSize("default_margin").width
                configuration: modelData
                onActivateConfiguration:
                {
                    switchPopupState()
                    Cura.MachineManager.applyRemoteConfiguration(configuration)
                }
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