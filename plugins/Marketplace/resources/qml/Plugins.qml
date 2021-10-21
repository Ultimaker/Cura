// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import Cura 1.7 as Cura
import UM 1.0 as UM

ScrollView
{
    clip: true

    Column
    {
        id: pluginColumn
        width: parent.width
        spacing: UM.Theme.getSize("default_margin").height

        Repeater
        {
            model: Cura.PackageList{}

            delegate: Rectangle
            {
                width: pluginColumn.width
                height: UM.Theme.getSize("card").height

                color: UM.Theme.getColor("main_background")
                radius: UM.Theme.getSize("default_radius").width

                Label
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left
                    anchors.leftMargin: (parent.height - height) / 2

                    text: model.package.displayName
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")
                }
            }
        }
        Button
        {
            id: loadMoreButton
            width: parent.width
            height: UM.Theme.getSize("card").height

            background: Rectangle
            {
                anchors.fill: parent
                radius: UM.Theme.getSize("default_radius").width
                color: UM.Theme.getColor("main_background")
            }

            Row
            {
                anchors.centerIn: parent

                spacing: UM.Theme.getSize("thin_margin").width

                UM.RecolorImage
                {
                    width: UM.Theme.getSize("small_button_icon").width
                    height: UM.Theme.getSize("small_button_icon").height
                    anchors.verticalCenter: loadMoreLabel.verticalCenter

                    source: UM.Theme.getIcon("ArrowDown")
                    color: UM.Theme.getColor("primary")
                }
                Label
                {
                    id: loadMoreLabel
                    text: catalog.i18nc("@button", "Load More")
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("primary")
                }
            }
        }
    }
}