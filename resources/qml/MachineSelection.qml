// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura
import "Menus"

ToolButton
{
    id: base
    property bool isNetworkPrinter: Cura.MachineManager.activeMachineNetworkKey != ""
    property bool printerConnected: Cura.MachineManager.printerConnected
    property var printerStatus: Cura.MachineManager.printerConnected ? "connected" : "disconnected"
    text: isNetworkPrinter ? Cura.MachineManager.activeMachineNetworkGroupName : Cura.MachineManager.activeMachineName

    tooltip: Cura.MachineManager.activeMachineName

    style: ButtonStyle
    {
        background: Rectangle
        {
            color:
            {
                if (control.pressed) {
                    return UM.Theme.getColor("sidebar_header_active");
                }
                else if (control.hovered) {
                    return UM.Theme.getColor("sidebar_header_hover");
                }
                else {
                    return UM.Theme.getColor("sidebar_header_bar");
                }
            }
            Behavior on color { ColorAnimation { duration: 50; } }

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

            PrinterStatusIcon
            {
                id: printerStatusIcon
                visible: printerConnected || isNetworkPrinter
                status: printerStatus
                anchors
                {
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                    leftMargin: UM.Theme.getSize("sidebar_margin").width
                }
            }

            Label
            {
                id: sidebarComboBoxLabel
                color: UM.Theme.getColor("sidebar_header_text_active")
                text: control.text;
                elide: Text.ElideRight;
                anchors.left: printerStatusIcon.visible ? printerStatusIcon.right : parent.left;
                anchors.leftMargin: printerStatusIcon.visible ? UM.Theme.getSize("sidebar_lining").width : UM.Theme.getSize("sidebar_margin").width
                anchors.right: downArrow.left;
                anchors.rightMargin: control.rightMargin;
                anchors.verticalCenter: parent.verticalCenter;
                font: UM.Theme.getFont("medium_bold")
            }
        }
        label: Label {}
    }

    menu: PrinterMenu { }
}
