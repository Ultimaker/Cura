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
            property string label: machineExtruderCount.properties.value > 1 ? catalog.i18nc("@label", "Hotend Temperature %1").arg(index + 1) : catalog.i18nc("@label", "Hotend Temperature")
            property string value: printerConnected ? Math.round(Cura.MachineManager.printerOutputDevices[0].hotendTemperatures[index]) + "°C" : ""
        }
    }
    Repeater
    {
        model: machineHeatedBed.properties.value == "True" ? 1 : 0
        delegate: Loader
        {
            sourceComponent: monitorItem
            property string label: catalog.i18nc("@label", "Bed Temperature")
            property string value: printerConnected ? Math.round(Cura.MachineManager.printerOutputDevices[0].bedTemperature) + "°C" : ""
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
        property string value: printerConnected ? Cura.MachineManager.printerOutputDevices[0].jobName : ""
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Printing Time")
        property string value: printerConnected ? getPrettyTime(Cura.MachineManager.printerOutputDevices[0].timeTotal) : ""
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Estimated time left")
        property string value: printerConnected ? getPrettyTime(Cura.MachineManager.printerOutputDevices[0].timeTotal - Cura.MachineManager.printerOutputDevices[0].timeElapsed) : ""
    }
    Loader
    {
        sourceComponent: monitorItem
        property string label: catalog.i18nc("@label", "Current Layer")
        property string value: printerConnected ? "0" : ""
    }

    Component
    {
        id: monitorItem

        Row
        {
            height: UM.Theme.getSize("setting_control").height
            Label
            {
                text: label
                color: printerConnected ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
                font: UM.Theme.getFont("default")
                width: base.width * 0.4
                elide: Text.ElideRight
                anchors.verticalCenter: parent.verticalCenter
            }
            Label
            {
                text: value
                color: printerConnected ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
                font: UM.Theme.getFont("default")
                anchors.verticalCenter: parent.verticalCenter
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