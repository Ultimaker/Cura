// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Rectangle {
    id: base

    UM.I18nCatalog { id: catalog; name:"cura"}

    width: childrenRect.width
    height: childrenRect.height
    color: "transparent"

    Connections
    {
        target: Printer
        onViewLegendItemsChanged:
        {
            legendItemRepeater.model = items
        }
    }

    Column
    {
        Repeater
        {
            id: legendItemRepeater

            Item {
                anchors.right: parent.right
                height: childrenRect.height
                width: childrenRect.width

                Rectangle {
                    id: swatch

                    anchors.right: parent.right
                    anchors.verticalCenter: label.verticalCenter
                    height: UM.Theme.getSize("setting_control").height / 2
                    width: height

                    color: modelData.color
                    border.width: UM.Theme.getSize("default_lining").width
                    border.color: UM.Theme.getColor("text_subtext")
                }
                Label {
                    id: label

                    text: modelData.title
                    font: UM.Theme.getFont("small")
                    color: UM.Theme.getColor("text_subtext")

                    anchors.right: swatch.left
                    anchors.rightMargin: UM.Theme.getSize("default_margin").width / 2
                }
            }
        }
    }
}
