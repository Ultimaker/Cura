// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.1
import UM 1.5 as UM

import Cura 1.1 as Cura

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
        height: childrenRect.height + 3 * UM.Theme.getSize("default_margin").width
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
            color: UM.Theme.getColor("main_background")
            Image
            {
                anchors.fill: parent
                fillMode: Image.PreserveAspectFit
                source: details === null ? "" : (details.icon_url || "../../images/placeholder.svg")
                mipmap: true
                height: UM.Theme.getSize("toolbox_thumbnail_large").height - 4 * UM.Theme.getSize("default_margin").height
                width: UM.Theme.getSize("toolbox_thumbnail_large").height - 4 * UM.Theme.getSize("default_margin").height
                sourceSize.height: height
                sourceSize.width: width
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
            }
            text: details === null ? "" : (details.name || "")
            font: UM.Theme.getFont("large_bold")
            width: contentWidth
            height: contentHeight
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
            UM.Label
            {
                text: catalog.i18nc("@label", "Version") + ":"
                color: UM.Theme.getColor("text_medium")
            }
            UM.Label
            {
                text: catalog.i18nc("@label", "Last updated") + ":"
                color: UM.Theme.getColor("text_medium")
            }
            UM.Label
            {
                text: catalog.i18nc("@label", "Brand") + ":"
                color: UM.Theme.getColor("text_medium")
                renderType: Text.NativeRendering
            }
            UM.Label
            {
                text: catalog.i18nc("@label", "Downloads") + ":"
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
            UM.Label
            {
                text: details === null ? "" : (details.version || catalog.i18nc("@label", "Unknown"))
            }

            UM.Label
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
            }
            UM.Label
            {
                text: details === null ? "" : "<a href=\"" + details.website + "\">" + details.author_name + "</a>"
                onLinkActivated: UM.UrlUtil.openUrl(link, ["http", "https"])
            }
            UM.Label
            {
                text: details === null ? "" : (details.download_count || catalog.i18nc("@label", "Unknown"))
            }
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
