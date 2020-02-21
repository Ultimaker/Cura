// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

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
            }
            text: details === null ? "" : (details.name || "")
            font: UM.Theme.getFont("large_bold")
            color: UM.Theme.getColor("text")
            width: contentWidth
            height: contentHeight
            renderType: Text.NativeRendering
        }

        SmallRatingWidget
        {
            anchors.left: title.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            anchors.verticalCenter: title.verticalCenter
            property var model: details
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
                text: catalog.i18nc("@label", "Your rating") + ":"
                visible: details.type == "plugin"
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text_medium")
                renderType: Text.NativeRendering
            }
            Label
            {
                text: catalog.i18nc("@label", "Version") + ":"
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text_medium")
                renderType: Text.NativeRendering
            }
            Label
            {
                text: catalog.i18nc("@label", "Last updated") + ":"
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text_medium")
                renderType: Text.NativeRendering
            }
            Label
            {
                text: catalog.i18nc("@label", "Author") + ":"
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text_medium")
                renderType: Text.NativeRendering
            }
            Label
            {
                text: catalog.i18nc("@label", "Downloads") + ":"
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
                top: title.bottom
                left: properties.right
                leftMargin: UM.Theme.getSize("default_margin").width
                topMargin: UM.Theme.getSize("default_margin").height
            }
            spacing: Math.floor(UM.Theme.getSize("narrow_margin").height)
            height: childrenRect.height
            RatingWidget
            {
                id: rating
                visible: details.type == "plugin"
                packageId: details.id != undefined ? details.id: ""
                userRating: details.user_rating != undefined ? details.user_rating: 0
                canRate: toolbox.isInstalled(details.id) && Cura.API.account.isLoggedIn

                onRated:
                {
                    toolbox.ratePackage(details.id, rating)
                    // HACK: This is a far from optimal solution, but without major refactoring, this is the best we can
                    // do. Since a rework of this is scheduled, it shouldn't live that long...
                    var index = toolbox.pluginsAvailableModel.find("id", details.id)
                    if(index != -1)
                    {
                        if(details.user_rating == 0)  // User never rated before.
                        {
                            toolbox.pluginsAvailableModel.setProperty(index, "num_ratings", details.num_ratings + 1)
                        }

                        toolbox.pluginsAvailableModel.setProperty(index, "user_rating", rating)


                        // Hack; This is because the current selection is an outdated copy, so we need to re-copy it.
                        base.selection = toolbox.pluginsAvailableModel.getItem(index)
                        return
                    }
                    index = toolbox.pluginsShowcaseModel.find("id", details.id)
                    if(index != -1)
                    {
                        if(details.user_rating == 0) // User never rated before.
                        {
                            toolbox.pluginsShowcaseModel.setProperty(index, "user_rating", rating)
                        }
                        toolbox.pluginsShowcaseModel.setProperty(index, "num_ratings", details.num_ratings + 1)

                        // Hack; This is because the current selection is an outdated copy, so we need to re-copy it.
                        base.selection = toolbox.pluginsShowcaseModel.getItem(index)
                    }
                }
            }
            Label
            {
                text: details === null ? "" : (details.version || catalog.i18nc("@label", "Unknown"))
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
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
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
            }
            Label
            {
                text:
                {
                    if (details === null)
                    {
                        return ""
                    }
                    else
                    {
                        return "<a href=\"" + details.website + "\">" + details.author_name + "</a>"
                    }
                }
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                linkColor: UM.Theme.getColor("text_link")
                onLinkActivated: Qt.openUrlExternally(link)
                renderType: Text.NativeRendering
            }
            Label
            {
                text: details === null ? "" : (details.download_count || catalog.i18nc("@label", "Unknown"))
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
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
