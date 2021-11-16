// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.1
import UM 1.5 as UM

import "../components"

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
            source: details && details.icon_url ? details.icon_url : "../../images/placeholder.svg"
            mipmap: true
            anchors
            {
                top: parent.top
                left: parent.left
                leftMargin: UM.Theme.getSize("wide_margin").width
                topMargin: UM.Theme.getSize("wide_margin").height
            }
        }

        UM.Label
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
            text: details && details.name ? details.name : ""
            font: UM.Theme.getFont("large_bold")
            color: UM.Theme.getColor("text_medium")
            wrapMode: Text.WordWrap
            width: parent.width
            height: UM.Theme.getSize("toolbox_property_label").height
        }
        UM.Label
        {
            id: description
            text: details && details.description ? details.description : ""
            color: UM.Theme.getColor("text_medium")
            anchors
            {
                top: title.bottom
                left: title.left
                topMargin: UM.Theme.getSize("default_margin").height
            }
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

            UM.Label
            {
                text: catalog.i18nc("@label", "Website") + ":"
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text_medium")
            }
            UM.Label
            {
                text: catalog.i18nc("@label", "Email") + ":"
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text_medium")
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
                right: parent.right
                rightMargin: UM.Theme.getSize("default_margin").width
                topMargin: UM.Theme.getSize("default_margin").height
            }
            spacing: Math.floor(UM.Theme.getSize("narrow_margin").height)

            UM.Label
            {
                text:
                {
                    if (details && details.website)
                    {
                        return "<a href=\"" + details.website + "\">" + details.website + "</a>"
                    }
                    return ""
                }
                width: parent.width
                elide: Text.ElideRight
                onLinkActivated: UM.UrlUtil.openUrl(link, ["https", "http"])
            }

            UM.Label
            {
                text:
                {
                    if (details && details.email)
                    {
                        return "<a href=\"mailto:" + details.email + "\">" + details.email + "</a>"
                    }
                    return ""
                }
                onLinkActivated: Qt.openUrlExternally(link)
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
