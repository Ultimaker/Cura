// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
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
        Rectangle
        {
            id: thumbnail
            width: UM.Theme.getSize("toolbox_thumbnail_medium").width
            height: UM.Theme.getSize("toolbox_thumbnail_medium").height
            anchors
            {
                top: parent.top
                left: parent.left
                leftMargin: UM.Theme.getSize("wide_margin").width
                topMargin: UM.Theme.getSize("wide_margin").height
            }
            color: white //Always a white background for image (regardless of theme).
            Image
            {
                anchors.fill: parent
                fillMode: Image.PreserveAspectFit
                source: details === null ? "" : (details.icon_url || "../images/logobot.svg")
                mipmap: true
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
            text: details === null ? "" : (details.name || "")
            font: UM.Theme.getFont("large")
            color: UM.Theme.getColor("text")
            wrapMode: Text.WordWrap
            width: parent.width
            height: UM.Theme.getSize("toolbox_property_label").height
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
            spacing: Math.floor(UM.Theme.getSize("narrow_margin").height)
            width: childrenRect.width
            height: childrenRect.height
            Label
            {
                text: catalog.i18nc("@label", "Version") + ":"
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text_medium")
            }
            Label
            {
                text: catalog.i18nc("@label", "Last updated") + ":"
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text_medium")
            }
            Label
            {
                text: catalog.i18nc("@label", "Author") + ":"
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text_medium")
            }
            Label
            {
                text: catalog.i18nc("@label", "Downloads") + ":"
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
            spacing: Math.floor(UM.Theme.getSize("narrow_margin").height)
            height: childrenRect.height
            Label
            {
                text: details === null ? "" : (details.version || catalog.i18nc("@label", "Unknown"))
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text")
            }
            Label
            {
                text:
                {
                    if (details === null)
                    {
                        return ""
                    }
                    var date = new Date(details.last_updated)
                    return date.toLocaleString(UM.Preferences.getValue("general/language"))
                }
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text")
            }
            Label
            {
                text:
                {
                    if (details === null)
                    {
                        return ""
                    }
                    if (details.author_email)
                    {
                        return "<a href=\"mailto:" + details.author_email+"?Subject=Cura: " + details.name + "\">" + details.author_name + "</a>"
                    }
                    else
                    {
                        return "<a href=\"" + details.website + "\">" + details.author_name + "</a>"
                    }
                }
                font: UM.Theme.getFont("very_small")
                color: UM.Theme.getColor("text")
                linkColor: UM.Theme.getColor("text_link")
                onLinkActivated: Qt.openUrlExternally(link)
            }
            Label
            {
                text: details === null ? "" : (details.download_count || catalog.i18nc("@label", "Unknown"))
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
