// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

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

    property bool selected: checked
    property bool printerTypeLabelAutoFit: false

    property var outputDevice: null
    property var printerTypesList: []

    property var updatePrinterTypesFunction: updatePrinterTypesList
    // This function converts the printer type string to another string.
    property var printerTypeLabelConversionFunction: Cura.MachineManager.getAbbreviatedMachineName

    function updatePrinterTypesList()
    {
        printerTypesList = (outputDevice != null) ? outputDevice.uniquePrinterTypes : []
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
                    autoFit: printerTypeLabelAutoFit
                    text: printerTypeLabelConversionFunction(modelData)
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
        border.color: machineSelectorButton.selected ? UM.Theme.getColor("primary") : "transparent"
    }

    Connections
    {
        target: outputDevice
        onUniqueConfigurationsChanged: updatePrinterTypesFunction()
    }

    Connections
    {
        target: Cura.MachineManager
        onOutputDevicesChanged: updatePrinterTypesFunction()
    }

    Component.onCompleted: updatePrinterTypesFunction()
}
