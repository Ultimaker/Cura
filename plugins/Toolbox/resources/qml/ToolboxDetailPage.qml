// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: base
    property var details: manager.packagesModel.items[0]
    anchors.fill: parent
    ToolboxBackColumn
    {
        id: sidebar
    }
    Rectangle
    {
        id: header
        anchors
        {
            left: sidebar.right
            right: parent.right
            rightMargin: UM.Theme.getSize("double_margin").width
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

        Label
        {
            id: title
            anchors
            {
                top: thumbnail.top
                left: thumbnail.right
                leftMargin: UM.Theme.getSize("default_margin").width
                right: parent.right
                rightMargin: UM.Theme.getSize("double_margin").width
                bottomMargin: UM.Theme.getSize("default_margin").height
            }
            text: details.name
            font: UM.Theme.getFont("large")
            wrapMode: Text.WordWrap
            width: parent.width
            height: UM.Theme.getSize("base_unit") * 2
        }

        Column
        {
            id: properties
            anchors
            {
                top: title.bottom
                left: title.left
                topMargin: UM.Theme.getSize("default_margin").height
            }
            spacing: Math.floor(UM.Theme.getSize("default_margin").height / 2)
            width: childrenRect.width
            Label
            {
                text: "Version:"
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text_medium")
            }
            Label
            {
                text: "Last Update:"
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text_medium")
            }
            Label
            {
                text: "Author:"
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text_medium")
            }
        }
        Column
        {
            id: values
            anchors
            {
                top: title.bottom
                left: properties.right
                leftMargin: UM.Theme.getSize("default_margin").width
                topMargin: UM.Theme.getSize("default_margin").height
            }
            spacing: Math.floor(UM.Theme.getSize("default_margin").height/2)
            width: UM.Theme.getSize("base_unit").width * 12
            Label
            {
                text: details.version
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text")
            }
            Label
            {
                text: Qt.formatDateTime(details.last_updated, "dd MMM yyyy")
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text")
            }
            Label
            {
                text: details.author_name
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text")
            }
        }
        Rectangle
        {
            color: UM.Theme.getColor("lining")
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
            anchors.bottom: parent.bottom
        }
    }
    ToolboxDetailList {
        anchors
        {
            top: header.bottom
            bottom: base.bottom
            left: header.left
            right: base.right
        }
    }
}
