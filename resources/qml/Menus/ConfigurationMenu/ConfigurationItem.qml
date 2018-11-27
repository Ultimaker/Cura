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
    signal activateConfiguration()

    height: childrenRect.height
    padding: 0 //Stupid QML button has spacing by default.
    rightPadding: 0
    leftPadding: 0

    property var textColor: checked ? UM.Theme.getColor("configuration_item_text_active") : UM.Theme.getColor("configuration_item_text")

    contentItem: Rectangle
    {
        height: childrenRect.height
        color: parent.checked ? UM.Theme.getColor("configuration_item_active") : UM.Theme.getColor("configuration_item")
        border.color: (parent.checked || parent.hovered) ? UM.Theme.getColor("primary") : UM.Theme.getColor("lining")
        border.width: UM.Theme.getSize("default_lining").width

        Column
        {
            id: contentColumn
            width: parent.width
            padding: UM.Theme.getSize("default_margin").width
            spacing: Math.round(UM.Theme.getSize("default_margin").height / 2)

            Row
            {
                id: extruderRow

                width: parent.width - 2 * parent.padding
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
                        mainColor: textColor
                    }
                }
            }

            //Buildplate row separator
            Rectangle
            {
                id: separator

                visible: buildplateInformation.visible
                width: parent.width - 2 * parent.padding
                height: visible ? Math.round(UM.Theme.getSize("thick_lining").height / 2) : 0
                color: textColor
            }

            Item
            {
                id: buildplateInformation
                width: parent.width - 2 * parent.padding
                height: childrenRect.height
                visible: configuration.buildplateConfiguration != ""

                UM.RecolorImage
                {
                    id: buildplateIcon
                    anchors.left: parent.left
                    width: UM.Theme.getSize("main_window_header_button_icon").width
                    height: UM.Theme.getSize("main_window_header_button_icon").height
                    sourceSize.width: width
                    sourceSize.height: height
                    source: UM.Theme.getIcon("buildplate")
                    color: textColor
                }

                Label
                {
                    id: buildplateLabel
                    anchors.left: buildplateIcon.right
                    anchors.verticalCenter: buildplateIcon.verticalCenter
                    anchors.leftMargin: Math.round(UM.Theme.getSize("default_margin").height / 2)
                    text: configuration.buildplateConfiguration
                    renderType: Text.NativeRendering
                    color: textColor
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
}