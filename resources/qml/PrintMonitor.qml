// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Column
{
    id: printMonitor
    property var connectedPrinter: printerConnected ? Cura.MachineManager.printerOutputDevices[0] : null

    Cura.ExtrudersModel
    {
        id: extrudersModel
        simpleNames: true
    }

    Rectangle
    {
        id: connectedPrinterHeader
        width: parent.width
        height: childrenRect.height + UM.Theme.getSize("default_margin").height * 2
        color: UM.Theme.getColor("setting_category")

        Label
        {
            id: connectedPrinterNameLabel
            text: printerConnected ? connectedPrinter.name : catalog.i18nc("@info:status", "No printer connected")
            font: UM.Theme.getFont("large")
            color: UM.Theme.getColor("text")
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
        }
        Label
        {
            id: connectedPrinterAddressLabel
            text: printerConnected ? connectedPrinter.address : ""
            font: UM.Theme.getFont("small")
            color: UM.Theme.getColor("text_inactive")
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.top: parent.top
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            horizontalAlignment: Text.AlignRight
        }
        Label
        {
            text: printerConnected ? connectedPrinter.connectionText : catalog.i18nc("@info:status", "The printer is not connected.")
            color: printerConnected && printerAcceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
            font: UM.Theme.getFont("very_small")
            wrapMode: Text.WordWrap
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.top: connectedPrinterNameLabel.bottom
        }
    }

    GridLayout
    {
        id: extrudersGrid
        columns: 2
        columnSpacing: UM.Theme.getSize("sidebar_lining_thin").width
        rowSpacing: UM.Theme.getSize("sidebar_lining_thin").height
        width: parent.width

        Repeater
        {
            model: machineExtruderCount.properties.value
            delegate: Rectangle
            {
                id: extruderRectangle
                color: UM.Theme.getColor("sidebar")
                width: extrudersGrid.width / 2 - UM.Theme.getSize("sidebar_lining_thin").width / 2
                height: UM.Theme.getSize("sidebar_extruder_box").height

                Text //Extruder name.
                {
                    text: machineExtruderCount.properties.value > 1 ? extrudersModel.getItem(index).name : catalog.i18nc("@label", "Hotend")
                    color: UM.Theme.getColor("text")
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    anchors.top: parent.top
                    anchors.topMargin: UM.Theme.getSize("default_margin").height
                }
                Text //Temperature indication.
                {
                    text: printerConnected ? Math.round(connectedPrinter.hotendTemperatures[index]) + "°C" : ""
                    font: UM.Theme.getFont("large")
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("default_margin").width
                    anchors.top: parent.top
                    anchors.topMargin: UM.Theme.getSize("default_margin").height
                }
            }
        }
    }

    Loader
    {
        sourceComponent: monitorSection
        property string label: catalog.i18nc("@label", "Temperatures")
    }
    Repeater
    {
        model: machineExtruderCount.properties.value
        delegate: Loader
        {
            sourceComponent: monitorItem
            property string label: machineExtruderCount.properties.value > 1 ? extrudersModel.getItem(index).name : catalog.i18nc("@label", "Hotend")
            property string value: printerConnected ? Math.round(connectedPrinter.hotendTemperatures[index]) + "°C" : ""
        }
    }
    Repeater
    {
        model: machineHeatedBed.properties.value == "True" ? 1 : 0
        delegate: Loader
        {
            sourceComponent: monitorItem
            property string label: catalog.i18nc("@label", "Build plate")
            property string value: printerConnected ? Math.round(connectedPrinter.bedTemperature) + "°C" : ""
        }
    }

    Loader
    {
        sourceComponent: monitorSection
        property string label: catalog.i18nc("@label", "Active print")
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Job Name")
        property string value: printerConnected ? connectedPrinter.jobName : ""
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Printing Time")
        property string value: printerConnected ? getPrettyTime(connectedPrinter.timeTotal) : ""
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Estimated time left")
        property string value: printerConnected ? getPrettyTime(connectedPrinter.timeTotal - connectedPrinter.timeElapsed) : ""
    }

    Component
    {
        id: monitorItem

        Row
        {
            height: UM.Theme.getSize("setting_control").height
            width: base.width - 2 * UM.Theme.getSize("default_margin").width
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width

            Label
            {
                width: parent.width * 0.4
                anchors.verticalCenter: parent.verticalCenter
                text: label
                color: printerConnected && printerAcceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
                font: UM.Theme.getFont("default")
                elide: Text.ElideRight
            }
            Label
            {
                width: parent.width * 0.6
                anchors.verticalCenter: parent.verticalCenter
                text: value
                color: printerConnected && printerAcceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
                font: UM.Theme.getFont("default")
                elide: Text.ElideRight
            }
        }
    }
    Component
    {
        id: monitorSection

        Rectangle
        {
            color: UM.Theme.getColor("setting_category")
            width: base.width - 2 * UM.Theme.getSize("default_margin").width
            height: UM.Theme.getSize("section").height

            Label
            {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                text: label
                font: UM.Theme.getFont("setting_category")
                color: UM.Theme.getColor("setting_category_text")
            }
        }
    }
}