// Copyright (c) 2016 Ultimaker B.V.
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

    Cura.ExtrudersModel { id: extrudersModel }

    Label
    {
        text: printerConnected ? connectedPrinter.connectionText : catalog.i18nc("@label", "The printer is not connected.")
        color: printerConnected && printerAcceptsCommands ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
        font: UM.Theme.getFont("default")
        wrapMode: Text.WordWrap
        width: base.width
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