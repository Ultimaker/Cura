// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: page
    property var details: base.selection || {}
    anchors.fill: parent
    ToolboxBackColumn
    {
        id: sidebar
    }
    Item
    {
        id: header
        anchors
        {
            left: sidebar.right
            right: parent.right
            rightMargin: UM.Theme.getSize("wide_margin").width
        }
        height: UM.Theme.getSize("toolbox_detail_header").height
        Image
        {
            id: thumbnail
            width: UM.Theme.getSize("toolbox_thumbnail_medium").width
            height: UM.Theme.getSize("toolbox_thumbnail_medium").height
            fillMode: Image.PreserveAspectFit
            source: details.icon_url || "../images/logobot.svg"
            mipmap: true
            anchors
            {
                top: parent.top
                left: parent.left
                leftMargin: UM.Theme.getSize("wide_margin").width
                topMargin: UM.Theme.getSize("wide_margin").height
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
                rightMargin: UM.Theme.getSize("wide_margin").width
                bottomMargin: UM.Theme.getSize("default_margin").height
            }
            text: details.name || ""
            font: UM.Theme.getFont("large_bold")
            wrapMode: Text.WordWrap
            width: parent.width
            height: UM.Theme.getSize("toolbox_property_label").height
            renderType: Text.NativeRendering
        }
        Label
        {
            id: description
            text: details.description || ""
            anchors
            {
                top: title.bottom
                left: title.left
                topMargin: UM.Theme.getSize("default_margin").height
            }
            renderType: Text.NativeRendering
        }
        Column
        {
            id: properties
            anchors
            {
                top: description.bottom
                left: description.left
                topMargin: UM.Theme.getSize("default_margin").height
            }
            spacing: Math.floor(UM.Theme.getSize("narrow_margin").height)
            width: childrenRect.width

            Label
            {
                text: catalog.i18nc("@label", "Website") + ":"
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text_medium")
                renderType: Text.NativeRendering
            }
            Label
            {
                text: catalog.i18nc("@label", "Email") + ":"
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text_medium")
                renderType: Text.NativeRendering
            }
        }
        Column
        {
            id: values
            anchors
            {
                top: description.bottom
                left: properties.right
                leftMargin: UM.Theme.getSize("default_margin").width
                topMargin: UM.Theme.getSize("default_margin").height
            }
            spacing: Math.floor(UM.Theme.getSize("narrow_margin").height)

            Label
            {
                text:
                {
                    if (details.website)
                    {
                        return "<a href=\"" + details.website + "\">" + details.website + "</a>"
                    }
                    return ""
                }
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                linkColor: UM.Theme.getColor("text_link")
                onLinkActivated: Qt.openUrlExternally(link)
                renderType: Text.NativeRendering
            }

            Label
            {
                text:
                {
                    if (details.email)
                    {
                        return "<a href=\"mailto:" + details.email + "\">" + details.email + "</a>"
                    }
                    return ""
                }
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                linkColor: UM.Theme.getColor("text_link")
                onLinkActivated: Qt.openUrlExternally(link)
                renderType: Text.NativeRendering
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
    ToolboxDetailList
    {
        anchors
        {
            top: header.bottom
            bottom: page.bottom
            left: header.left
            right: page.right
        }
    }
}
