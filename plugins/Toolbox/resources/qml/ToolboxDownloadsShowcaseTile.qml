// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    width: UM.Theme.getSize("toolbox_thumbnail_large").width
    height: UM.Theme.getSize("toolbox_thumbnail_large").width
    visible:
    {
        if (toolbox.viewCategory == "material" && model.packages_count)
        {
            return model.packages_count > 0
        }
        else
        {
            return true
        }
    }
    Rectangle
    {
        color: "white"
        width: UM.Theme.getSize("toolbox_thumbnail_medium").width
        height: UM.Theme.getSize("toolbox_thumbnail_medium").height
        border
        {
            width: UM.Theme.getSize("default_lining").width
            color: UM.Theme.getColor("lining")
        }
        anchors
        {
            top: parent.top
            horizontalCenter: parent.horizontalCenter
        }
        Image {
            anchors.centerIn: parent
            width: UM.Theme.getSize("toolbox_thumbnail_medium").width - 2 * UM.Theme.getSize("default_margin")
            height: UM.Theme.getSize("toolbox_thumbnail_medium").height - 2 * UM.Theme.getSize("default_margin")
            fillMode: Image.PreserveAspectFit
            source: model.icon_url || "../images/logobot.svg"
        }
    }
    Label
    {
        text: model.name
        anchors
        {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
        }
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        height: UM.Theme.getSize("toolbox_heading_label").height
        width: parent.width
        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("medium_bold")
    }
    MouseArea
    {
        anchors.fill: parent
        onClicked:
        {
            switch(toolbox.viewCategory)
            {
                case "material":
                    toolbox.viewSelection = model.name
                    toolbox.viewPage = "author"
                    toolbox.filterModelByProp("authors", "name", model.name)
                    toolbox.filterModelByProp("packages", "author_name", model.name)
                    break
                default:
                    toolbox.viewSelection = model.id
                    toolbox.viewPage = "detail"
                    toolbox.filterModelByProp("authors", "name", model.author_name)
                    toolbox.filterModelByProp("packages", "id", model.id)
                    break
            }
        }
    }
}
