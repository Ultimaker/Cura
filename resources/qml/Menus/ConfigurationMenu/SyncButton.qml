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
    property var outputDevice: Cura.MachineManager.printerOutputDevices[0] != null ? Cura.MachineManager.printerOutputDevices[0] : null
    text: catalog.i18nc("@label:sync indicator", "No match")
    width: parent.width
    height: parent.height

    function updateOnSync()
    {
        for (var index in outputDevice.uniqueConfigurations)
        {
            var configuration = outputDevice.uniqueConfigurations[index]
            if (Cura.MachineManager.matchesConfiguration(configuration))
            {
                base.text = catalog.i18nc("@label:sync indicator", "Matched")
                return
            }
        }
        base.text = catalog.i18nc("@label:sync indicator", "No match")
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
            Label
            {
                id: sidebarComboBoxLabel
                color: UM.Theme.getColor("sidebar_header_text_active")
                text: control.text
                elide: Text.ElideRight
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                anchors.right: downArrow.left
                anchors.rightMargin: control.rightMargin
                anchors.verticalCenter: parent.verticalCenter;
                font: UM.Theme.getFont("medium_bold")
            }
        }
        label: Label {}
    }

    onClicked:
    {
        panelVisible = !panelVisible
    }

    Connections {
        target: outputDevice
        onUniqueConfigurationsChanged: {
            updateOnSync()
        }
    }

    Connections {
        target: Cura.MachineManager
        onCurrentConfigurationChanged: {
            updateOnSync()
        }
    }
}