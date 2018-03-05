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
    border.color: UM.Theme.getColor("sidebar_lining_thin")

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
                }
                Component.onCompleted: {print("ELEMENTOS:", repeater.model.count)}
            }
        }

        //Buildplate row separator
        Rectangle {
            id: separator

            visible: buildplateInformation.visible
            width: parent.width - 2 * parent.padding
            height: visible ? Math.round(UM.Theme.getSize("sidebar_lining_thin").height / 2) : 0
            color: UM.Theme.getColor("sidebar_lining_thin")
        }

        Item
        {
            id: buildplateInformation
            width: parent.width - 2 * parent.padding
            height: childrenRect.height
            visible: configuration.buildplateConfiguration != ""

            UM.RecolorImage {
                id: buildplateIcon
                anchors.left: parent.left
                anchors.verticalCenter: parent.verticalCenter
                width: UM.Theme.getSize("standard_arrow").width
                height: UM.Theme.getSize("standard_arrow").height
                sourceSize.width: width
                sourceSize.height: height
                source: UM.Theme.getIcon("extruder_button")

                color: "black"
            }

            Label
            {
                id: buildplateLabel
                anchors.left: buildplateIcon.right
                anchors.verticalCenter: parent.verticalCenter
                anchors.leftMargin: Math.round(UM.Theme.getSize("default_margin").height / 2)
                text: configuration.buildplateConfiguration
            }
        }
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