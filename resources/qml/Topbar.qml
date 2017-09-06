// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura
import "Menus"

Rectangle
{
    id: base
    anchors.left: parent.left
    anchors.right: parent.right
    height: UM.Theme.getSize("sidebar_header").height
    color: UM.Theme.getColor("sidebar_header_bar")

    property bool printerConnected: Cura.MachineManager.printerOutputDevices.length != 0
    property bool printerAcceptsCommands: printerConnected && Cura.MachineManager.printerOutputDevices[0].acceptsCommands
    property bool monitoringPrint: false
    signal startMonitoringPrint()
    signal stopMonitoringPrint()
    UM.I18nCatalog
    {
        id: catalog
        name:"cura"
    }

    Row
    {
        anchors.left: parent.left
        anchors.right: machineSelection.left
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        spacing: UM.Theme.getSize("default_margin").width

        Button
        {
            id: showSettings
            height: UM.Theme.getSize("sidebar_header").height
            onClicked: base.stopMonitoringPrint()
            iconSource: UM.Theme.getIcon("tab_settings");
            property color overlayColor: "transparent"
            property string overlayIconSource: ""
            text: catalog.i18nc("@title:tab", "Prepare")
            checkable: true
            checked: !base.monitoringPrint
            exclusiveGroup: sidebarHeaderBarGroup

            style:  UM.Theme.styles.topbar_header_tab
        }

        Button
        {
            id: showMonitor
            height: UM.Theme.getSize("sidebar_header").height
            onClicked: base.startMonitoringPrint()
            text: catalog.i18nc("@title:tab", "Monitor")
            iconSource: UM.Theme.getIcon("tab_monitor")
            property color overlayColor:
            {
                if(!printerAcceptsCommands)
                {
                    return UM.Theme.getColor("status_unknown");
                }

                if(Cura.MachineManager.printerOutputDevices[0].printerState == "maintenance")
                {
                    return UM.Theme.getColor("status_busy");
                }
                switch(Cura.MachineManager.printerOutputDevices[0].jobState)
                {
                    case "printing":
                    case "pre_print":
                    case "wait_cleanup":
                    case "pausing":
                    case "resuming":
                        return UM.Theme.getColor("status_busy");
                    case "ready":
                    case "":
                        return UM.Theme.getColor("status_ready");
                    case "paused":
                        return UM.Theme.getColor("status_paused");
                    case "error":
                        return UM.Theme.getColor("status_stopped");
                    case "offline":
                        return UM.Theme.getColor("status_offline");
                    default:
                        return UM.Theme.getColor("text_reversed");
                }
            }
            property string overlayIconSource:
            {
                if(!printerConnected)
                {
                    return "";
                }
                else if(!printerAcceptsCommands)
                {
                    return UM.Theme.getIcon("tab_status_unknown");
                }

                if(Cura.MachineManager.printerOutputDevices[0].printerState == "maintenance")
                {
                    return UM.Theme.getIcon("tab_status_busy");
                }

                switch(Cura.MachineManager.printerOutputDevices[0].jobState)
                {
                    case "printing":
                    case "pre_print":
                    case "pausing":
                    case "resuming":
                        return UM.Theme.getIcon("tab_status_busy");
                    case "wait_cleanup":
                        return UM.Theme.getIcon("tab_status_finished");
                    case "ready":
                    case "":
                        return UM.Theme.getIcon("tab_status_connected")
                    case "paused":
                        return UM.Theme.getIcon("tab_status_paused")
                    case "error":
                        return UM.Theme.getIcon("tab_status_stopped")
                    default:
                        return ""
                }
            }

            checkable: true
            checked: base.monitoringPrint
            exclusiveGroup: sidebarHeaderBarGroup

            style:  UM.Theme.styles.topbar_header_tab
        }

        ExclusiveGroup { id: sidebarHeaderBarGroup }
    }

    ToolButton
    {
        id: machineSelection
        text: Cura.MachineManager.activeMachineName

        width: UM.Theme.getSize("sidebar").width;
        height: UM.Theme.getSize("sidebar_header").height
        tooltip: Cura.MachineManager.activeMachineName

        anchors.verticalCenter: parent.verticalCenter
        anchors.right: parent.right
        style: ButtonStyle
        {
            background: Rectangle
            {
                color:
                {
                    if(control.pressed)
                    {
                        return UM.Theme.getColor("sidebar_header_active");
                    } else if(control.hovered)
                    {
                        return UM.Theme.getColor("sidebar_header_hover");
                    } else
                    {
                        return UM.Theme.getColor("sidebar_header_bar");
                    }
                }
                Behavior on color { ColorAnimation { duration: 50; } }

                Rectangle
                {
                    id: underline;

                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: UM.Theme.getSize("sidebar_header_highlight").height
                    color: UM.Theme.getColor("sidebar_header_highlight_hover")
                    visible: control.hovered || control.pressed
                }

                UM.RecolorImage
                {
                    id: downArrow
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("default_margin").width
                    width: UM.Theme.getSize("standard_arrow").width
                    height: UM.Theme.getSize("standard_arrow").height
                    sourceSize.width: width
                    sourceSize.height: width
                    color: UM.Theme.getColor("text_emphasis")
                    source: UM.Theme.getIcon("arrow_bottom")
                }
                Label
                {
                    id: sidebarComboBoxLabel
                    color: UM.Theme.getColor("sidebar_header_text_active")
                    text: control.text;
                    elide: Text.ElideRight;
                    anchors.left: parent.left;
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    anchors.right: downArrow.left;
                    anchors.rightMargin: control.rightMargin;
                    anchors.verticalCenter: parent.verticalCenter;
                    font: UM.Theme.getFont("large")
                }
            }
            label: Label {}
        }

        menu: PrinterMenu { }
    }
}
