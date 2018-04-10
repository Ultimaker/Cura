// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    width: UM.Theme.getSize("toolbox_thumbnail_large").width
    height: UM.Theme.getSize("toolbox_thumbnail_large").width
    Rectangle
    {
        color: "white"
        width: UM.Theme.getSize("toolbox_thumbnail_medium").width
        height: UM.Theme.getSize("toolbox_thumbnail_medium").height
        border.width: 1
        border.color: UM.Theme.getColor("text_medium")
        anchors
        {
            top: parent.top
            horizontalCenter: parent.horizontalCenter
        }
        Image {
            anchors.centerIn: parent
            width: UM.Theme.getSize("toolbox_thumbnail_medium").width - 26
            height: UM.Theme.getSize("toolbox_thumbnail_medium").height - 26
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
        height: UM.Theme.getSize("base_unit").width * 4
        width: parent.width
        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("medium_bold")
    }
    MouseArea
    {
        anchors.fill: parent
        onClicked: {
            if ( manager.viewCategory == "material" )
            {
                manager.viewSelection = model.name
                manager.viewPage = "author"
                manager.filterPackages("author_name", model.name)
            }
            else
            {
                manager.viewSelection = model.id
                manager.viewPage = "detail"
                manager.filterPackages("id", model.id)
            }
        }
    }
}
