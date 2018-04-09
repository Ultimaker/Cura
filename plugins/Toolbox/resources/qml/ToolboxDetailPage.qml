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
    property var details: manager.packagesModel.items[0]
    id: base
    anchors.fill: parent
    Item
    {
        id: sidebar
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
            UM.RecolorImage
            {
                id: backArrow
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                width: UM.Theme.getSize("standard_arrow").width
                height: UM.Theme.getSize("standard_arrow").height
                sourceSize.width: width
                sourceSize.height: height
                color: UM.Theme.getColor("text")
                source: UM.Theme.getIcon("arrow_left")
            }
            width: UM.Theme.getSize("base_unit").width * 4
            height: UM.Theme.getSize("base_unit").height * 2
            onClicked:
            {
                manager.viewPage = "overview"
                manager.filterPackages("type", manager.viewCategory)
            }
            style: ButtonStyle
            {
                background: Rectangle
                {
                    color: "transparent"
                }
                label: Label
                {
                    text: control.text
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default_bold")
                    horizontalAlignment: Text.AlignRight
                    width: control.width
                }
            }
        }
    }

    Rectangle
    {
        id: header
        anchors
        {
            left: sidebar.right
            right: parent.right
        }
        height: UM.Theme.getSize("base_unit").height * 12
        Image
        {
            id: thumbnail
            width: UM.Theme.getSize("toolbox_thumbnail_medium").width
            height: UM.Theme.getSize("toolbox_thumbnail_medium").height
            fillMode: Image.PreserveAspectFit
            source: details.icon_url || "../images/logobot.svg"
            anchors
            {
                top: parent.top
                left: parent.left
                leftMargin: UM.Theme.getSize("double_margin").width
                topMargin: UM.Theme.getSize("double_margin").height
            }
        }
        Column
        {
            anchors
            {
                top: thumbnail.top
                left: thumbnail.right
                leftMargin: UM.Theme.getSize("default_margin").width
                right: parent.right
                rightMargin: UM.Theme.getSize("double_margin").width
            }
            spacing: Math.floor(UM.Theme.getSize("default_margin").height/2)
            Label
            {
                text: details.name
                font: UM.Theme.getFont("large")
                wrapMode: Text.WordWrap
                width: parent.width
            }
            Label
            {
                text: details.description
                font: UM.Theme.getFont("default")
                wrapMode: Text.WordWrap
                width: parent.width
            }
            Label
            {
                text: "Author: " + details.author_name
                font: UM.Theme.getFont("small")
                wrapMode: Text.WordWrap
                width: parent.width
                // TODO: Add mail icon.
            }
        }
    }
    ToolboxDetailList {
        anchors
        {
            right: header.right
            top: header.bottom

            left: header.left
            bottom: base.bottom

        }
    }
}
