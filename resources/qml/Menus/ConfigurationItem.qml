// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.2 as UM
import Cura 1.0 as Cura

Rectangle
{
    id: configurationItem

    property var printer: null
    signal configurationSelected()

    anchors.leftMargin: 25
    border.width: UM.Theme.getSize("default_lining").width
    border.color: "black"

    Rectangle
    {
        id: printerInformation

        Label
        {
            text: printer.name
        }
    }

    Rectangle
    {
        id: extruderInformation

        Row
        {
            id: extrudersRow

            Repeater
            {
                model: printer.extruders
                delegate: Item
                {
                    id: extruderInfo

                    width: Math.round(parent.width / 2)
                    height: childrenRect.height
                    Label
                    {
                        id: materialLabel
                        text: modelData.activeMaterial != null ? modelData.activeMaterial.name : ""
                        elide: Text.ElideRight
                        width: parent.width
                        font: UM.Theme.getFont("very_small")
                    }
                    Label
                    {
                        id: printCoreLabel
                        text: modelData.hotendID
                        anchors.top: materialLabel.bottom
                        elide: Text.ElideRight
                        width: parent.width
                        font: UM.Theme.getFont("very_small")
                        opacity: 0.5
                    }
                }
            }
        }
    }

//    Rectangle
//    {
//        id: buildplateInformation
//
//        Label
//        {
//            text: printer.name + "-" + printer.type
//        }
//    }

    MouseArea
    {
        id: mouse
        anchors.fill: parent
        onClicked: configurationSelected()
        hoverEnabled: true
    }
}