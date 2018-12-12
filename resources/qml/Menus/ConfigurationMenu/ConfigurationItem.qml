// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

Button
{
    id: configurationItem

    property var configuration: null
    hoverEnabled: true

    height: background.height

    background: Rectangle
    {
        height: childrenRect.height
        color: parent.hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("action_button")
        border.color: (parent.checked || parent.hovered) ? UM.Theme.getColor("primary") : UM.Theme.getColor("lining")
        border.width: parent.checked ? UM.Theme.getSize("thick_lining").width : UM.Theme.getSize("default_lining").width
        radius: UM.Theme.getSize("default_radius").width

        Column
        {
            id: contentColumn
            width: parent.width
            padding: UM.Theme.getSize("wide_margin").width
            spacing: UM.Theme.getSize("narrow_margin").height

            Row
            {
                id: extruderRow

                anchors
                {
                    left: parent.left
                    leftMargin: parent.padding
                    right: parent.right
                    rightMargin: parent.padding
                }
                height: childrenRect.height

                spacing: UM.Theme.getSize("default_margin").width

                Repeater
                {
                    id: repeater
                    height: childrenRect.height
                    model: configuration.extruderConfigurations
                    delegate: PrintCoreConfiguration
                    {
                        width: Math.round(parent.width / 2)
                        printCoreConfiguration: modelData
                    }
                }
            }

            //Buildplate row separator
            Rectangle
            {
                id: separator

                visible: buildplateInformation.visible
                anchors
                {
                    left: parent.left
                    leftMargin: parent.padding
                    right: parent.right
                    rightMargin: parent.padding
                }
                height: visible ? Math.round(UM.Theme.getSize("default_lining").height / 2) : 0
                color: UM.Theme.getColor("lining")
            }

            Item
            {
                id: buildplateInformation

                anchors
                {
                    left: parent.left
                    leftMargin: parent.padding
                    right: parent.right
                    rightMargin: parent.padding
                }
                height: childrenRect.height
                visible: configuration.buildplateConfiguration != ""

                UM.RecolorImage
                {
                    id: buildplateIcon
                    anchors.left: parent.left
                    width: UM.Theme.getSize("main_window_header_button_icon").width
                    height: UM.Theme.getSize("main_window_header_button_icon").height
                    source: UM.Theme.getIcon("buildplate")
                    color: UM.Theme.getColor("text")
                }

                Label
                {
                    id: buildplateLabel
                    anchors.left: buildplateIcon.right
                    anchors.verticalCenter: buildplateIcon.verticalCenter
                    anchors.leftMargin: Math.round(UM.Theme.getSize("default_margin").height / 2)
                    text: configuration.buildplateConfiguration
                    renderType: Text.NativeRendering
                    color: UM.Theme.getColor("text")
                }
            }
        }

        Connections
        {
            target: Cura.MachineManager
            onCurrentConfigurationChanged:
            {
                configurationItem.checked = Cura.MachineManager.matchesConfiguration(configuration)
            }
        }

        Component.onCompleted:
        {
            configurationItem.checked = Cura.MachineManager.matchesConfiguration(configuration)
        }
    }

    onClicked:
    {
        Cura.MachineManager.applyRemoteConfiguration(configuration)
    }
}