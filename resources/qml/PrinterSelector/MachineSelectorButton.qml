// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Button
{
    id: machineSelectorButton

    width: parent.width
    height: UM.Theme.getSize("action_button").height
    leftPadding: UM.Theme.getSize("thick_margin").width
    rightPadding: UM.Theme.getSize("thick_margin").width
    checkable: true
    hoverEnabled: true

    property var outputDevice: null
    property var printerTypesList: []

    function updatePrinterTypesList()
    {
        printerTypesList = (checked && (outputDevice != null)) ? outputDevice.uniquePrinterTypes : []
    }

    contentItem: Item
    {
        width: machineSelectorButton.width - machineSelectorButton.leftPadding
        height: UM.Theme.getSize("action_button").height

        Label
        {
            id: buttonText
            anchors
            {
                left: parent.left
                right: printerTypes.left
                verticalCenter: parent.verticalCenter
            }
            text: machineSelectorButton.text
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("medium")
            visible: text != ""
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
        }

        Row
        {
            id: printerTypes
            width: childrenRect.width

            anchors
            {
                right: parent.right
                verticalCenter: parent.verticalCenter
            }
            spacing: UM.Theme.getSize("narrow_margin").width

            Repeater
            {
                model: printerTypesList
                delegate: Cura.PrinterTypeLabel
                {
                    text: Cura.MachineManager.getAbbreviatedMachineName(modelData)
                }
            }
        }
    }

    background: Rectangle
    {
        id: backgroundRect
        color: machineSelectorButton.hovered ? UM.Theme.getColor("action_button_hovered") : "transparent"
        radius: UM.Theme.getSize("action_button_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        border.color: machineSelectorButton.checked ? UM.Theme.getColor("primary") : "transparent"
    }

    onClicked:
    {
        toggleContent()
        Cura.MachineManager.setActiveMachine(model.id)
    }

    Connections
    {
        target: outputDevice
        onUniqueConfigurationsChanged: updatePrinterTypesList()
    }

    Connections
    {
        target: Cura.MachineManager
        onOutputDevicesChanged: updatePrinterTypesList()
    }

    Component.onCompleted: updatePrinterTypesList()
}
