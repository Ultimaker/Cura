// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

Rectangle
{
    id: configurationItem

    property var configuration: null
    signal configurationSelected()

    height: childrenRect.height
    border.width: UM.Theme.getSize("default_lining").width
    border.color: "black"

    Column
    {
        id: contentColumn
        padding: UM.Theme.getSize("default_margin").width
        spacing: UM.Theme.getSize("default_margin").height

        Label
        {
            text: configuration.printerType
        }

        Row
        {
            id: extruderRow

            width: parent.width
            height: childrenRect.height

            spacing: UM.Theme.getSize("default_margin").width

            Repeater
            {
                height: childrenRect.height
                model: configuration.extruderConfigurations
                delegate: PrintCoreConfiguration
                {
                    printCoreConfiguration: modelData
                }
            }
        }

//        Rectangle
//        {
//            id: buildplateInformation
//
//            Label
//            {
//                text: configuration.buildplateConfiguration
//            }
//        }
    }

    MouseArea
    {
        id: mouse
        anchors.fill: parent
        onClicked: configurationSelected()
        hoverEnabled: true
        onEntered: parent.border.color = UM.Theme.getColor("primary_hover")
        onExited: parent.border.color = "black"
    }
}