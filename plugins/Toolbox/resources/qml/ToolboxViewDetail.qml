// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

Item
{
    id: base
    anchors.fill: parent
    Item
    {
        id: backMargin
        height: parent.height
        width: UM.Theme.getSize("base_unit").width * 6
        anchors
        {
            top: parent.top
            left: parent.left
            topMargin: UM.Theme.getSize("double_margin").height
            leftMargin: UM.Theme.getSize("default_margin").width
            rightMargin: UM.Theme.getSize("default_margin").width
        }
        Button
        {
            text: "Back"
            onClicked: manager.detailView = false
        }
    }
    ScrollView
    {
        id: scroll
        frameVisible: false
        anchors.right: base.right
        anchors.left: backMargin.right
        height: parent.height
        style: UM.Theme.styles.scrollview
        Column
        {
            width: scroll.width
            spacing: UM.Theme.getSize("base_unit").height
            height: childrenRect.height + (UM.Theme.getSize("double_margin").height * 2)
            anchors
            {
                fill: parent
                topMargin: UM.Theme.getSize("double_margin").height
                bottomMargin: UM.Theme.getSize("double_margin").height
                leftMargin: UM.Theme.getSize("double_margin").width
                rightMargin: UM.Theme.getSize("double_margin").width
            }
            Rectangle
            {
                width: parent.width
                height: UM.Theme.getSize("base_unit").height * 12
                color: "transparent"
                Rectangle
                {
                    id: thumbnail
                    width: UM.Theme.getSize("toolbox_thumbnail_medium").width
                    height: UM.Theme.getSize("toolbox_thumbnail_medium").height
                    color: "white"
                    border.width: 1
                }
            }
            ToolboxDetailTile {}
            ToolboxDetailTile {}
            ToolboxDetailTile {}
            ToolboxDetailTile {}
            ToolboxDetailTile {}
            ToolboxDetailTile {}
            ToolboxDetailTile {}
            ToolboxDetailTile {}
            ToolboxDetailTile {}
            ToolboxDetailTile {}
            ToolboxDetailTile {}
        }
    }
}
