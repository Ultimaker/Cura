// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura
import "Menus"
import "Menus/ConfigurationMenu"

Rectangle
{
    id: base

    property int currentModeIndex
    property bool hideSettings: PrintInformation.preSliced
    property bool hideView: Cura.MachineManager.activeMachineName == ""

    // Is there an output device for this printer?
    property bool isNetworkPrinter: Cura.MachineManager.activeMachineNetworkKey != ""
    property bool printerConnected: Cura.MachineManager.printerConnected
    property bool printerAcceptsCommands: printerConnected && Cura.MachineManager.printerOutputDevices[0].acceptsCommands
    property var connectedPrinter: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null

    property variant printDuration: PrintInformation.currentPrintTime
    property variant printMaterialLengths: PrintInformation.materialLengths
    property variant printMaterialWeights: PrintInformation.materialWeights
    property variant printMaterialCosts: PrintInformation.materialCosts
    property variant printMaterialNames: PrintInformation.materialNames

    color: UM.Theme.getColor("sidebar")
    UM.I18nCatalog { id: catalog; name:"cura"}

    Timer {
        id: tooltipDelayTimer
        interval: 500
        repeat: false
        property var item
        property string text

        onTriggered:
        {
            base.showTooltip(base, {x: 0, y: item.y}, text);
        }
    }

    function showTooltip(item, position, text)
    {
        tooltip.text = text;
        position = item.mapToItem(base, position.x - UM.Theme.getSize("default_arrow").width, position.y);
        tooltip.show(position);
    }

    function hideTooltip()
    {
        tooltip.hide();
    }

    function strPadLeft(string, pad, length) {
        return (new Array(length + 1).join(pad) + string).slice(-length);
    }

    function getPrettyTime(time)
    {
        var hours = Math.floor(time / 3600)
        time -= hours * 3600
        var minutes = Math.floor(time / 60);
        time -= minutes * 60
        var seconds = Math.floor(time);

        var finalTime = strPadLeft(hours, "0", 2) + ':' + strPadLeft(minutes,'0',2)+ ':' + strPadLeft(seconds,'0',2);
        return finalTime;
    }

    MouseArea
    {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons

        onWheel:
        {
            wheel.accepted = true;
        }
    }

    MachineSelection
    {
        id: machineSelection
        width: base.width - configSelection.width - separator.width
        height: UM.Theme.getSize("sidebar_header").height
        anchors.top: base.top
        anchors.left: parent.left
    }

    Rectangle
    {
        id: separator
        visible: configSelection.visible
        width: visible ? Math.round(UM.Theme.getSize("sidebar_lining_thin").height / 2) : 0
        height: UM.Theme.getSize("sidebar_header").height
        color: UM.Theme.getColor("sidebar_lining_thin")
        anchors.left: machineSelection.right
    }

    ConfigurationSelection
    {
        id: configSelection
        visible: isNetworkPrinter && printerConnected
        width: visible ? Math.round(base.width * 0.15) : 0
        height: UM.Theme.getSize("sidebar_header").height
        anchors.top: base.top
        anchors.right: parent.right
        panelWidth: base.width
    }

    Loader
    {
        id: controlItem
        anchors.bottom: footerSeparator.top
        anchors.top: machineSelection.bottom
        anchors.left: base.left
        anchors.right: base.right
        sourceComponent:
        {
            if(connectedPrinter != null)
            {
                if(connectedPrinter.controlItem != null)
                {
                    return connectedPrinter.controlItem
                }
            }
            return null
        }
    }

    Loader
    {
        anchors.bottom: footerSeparator.top
        anchors.top: machineSelection.bottom
        anchors.left: base.left
        anchors.right: base.right
        source:
        {
            if(controlItem.sourceComponent == null)
            {
                return "PrintMonitor.qml"
            }
            else
            {
                return ""
            }
        }
    }

    Rectangle
    {
        id: footerSeparator
        width: parent.width
        height: UM.Theme.getSize("sidebar_lining").height
        color: UM.Theme.getColor("sidebar_lining")
        anchors.bottom: monitorButton.top
        anchors.bottomMargin: UM.Theme.getSize("sidebar_margin").height
    }

    // MonitorButton is actually the bottom footer panel.
    MonitorButton
    {
        id: monitorButton
        implicitWidth: base.width
        anchors.bottom: parent.bottom
    }

    SidebarTooltip
    {
        id: tooltip
    }

    UM.SettingPropertyProvider
    {
        id: machineExtruderCount

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_extruder_count"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    UM.SettingPropertyProvider
    {
        id: machineHeatedBed

        containerStackId: Cura.MachineManager.activeMachineId
        key: "machine_heated_bed"
        watchedProperties: [ "value" ]
        storeIndex: 0
    }

    // Make the ConfigurationSelector react when the global container changes, otherwise if Cura is not connected to the printer,
    // switching printers make no reaction
    Connections
    {
        target: Cura.MachineManager
        onGlobalContainerChanged:
        {
            base.isNetworkPrinter = Cura.MachineManager.activeMachineNetworkKey != ""
            base.printerConnected = Cura.MachineManager.printerOutputDevices.length != 0
        }
    }
}
