// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Button
{
    id: base
    property var outputDevice: null
    property var matched: updateOnSync()
    text: matched == true ? catalog.i18nc("@label:extruder label", "Yes") : catalog.i18nc("@label:extruder label", "No")
    width: parent.width
    height: parent.height

    function updateOnSync()
    {
        if (outputDevice != undefined)
        {
            for (var index in outputDevice.uniqueConfigurations)
            {
                var configuration = outputDevice.uniqueConfigurations[index]
                if (Cura.MachineManager.matchesConfiguration(configuration))
                {
                    base.matched = true;
                    return;
                }
            }
        }
        base.matched = false;
    }

    style: ButtonStyle
    {
        background: Rectangle
        {
            color:
            {
                if(control.pressed)
                {
                    return UM.Theme.getColor("sidebar_header_active");
                }
                else if(control.hovered)
                {
                    return UM.Theme.getColor("sidebar_header_hover");
                }
                else
                {
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
                sourceSize.height: height
                color: UM.Theme.getColor("text_emphasis")
                source: UM.Theme.getIcon("arrow_bottom")
            }
            UM.RecolorImage
            {
                id: sidebarComboBoxLabel
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                anchors.verticalCenter: parent.verticalCenter;

                width: UM.Theme.getSize("printer_sync_icon").width
                height: UM.Theme.getSize("printer_sync_icon").height

                color:  control.matched ? UM.Theme.getColor("printer_config_matched") : UM.Theme.getColor("printer_config_mismatch")
                source: UM.Theme.getIcon("tab_status_connected")
                sourceSize.width: width
                sourceSize.height: height
            }
        }
        label: Label {}
    }

    Connections
    {
        target: outputDevice
        onUniqueConfigurationsChanged: updateOnSync()
    }

    Connections
    {
        target: Cura.MachineManager
        onCurrentConfigurationChanged: updateOnSync()
        onOutputDevicesChanged: updateOnSync()
    }
}