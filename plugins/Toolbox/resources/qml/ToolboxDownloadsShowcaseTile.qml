// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtGraphicalEffects 1.0
import UM 1.1 as UM

Rectangle
{
    property int packageCount: toolbox.viewCategory == "material" ? toolbox.getTotalNumberOfMaterialPackagesByAuthor(model.id) : 1
    property int installedPackages: toolbox.viewCategory == "material" ? toolbox.getNumberOfInstalledPackagesByAuthor(model.id) : (toolbox.isInstalled(model.id) ? 1 : 0)
    id: tileBase
    width: UM.Theme.getSize("toolbox_thumbnail_large").width + (2 * UM.Theme.getSize("default_lining").width)
    height: thumbnail.height + packageNameBackground.height + (2 * UM.Theme.getSize("default_lining").width)
    border.width: UM.Theme.getSize("default_lining").width
    border.color: UM.Theme.getColor("lining")
    color: "transparent"
    Rectangle
    {
        id: thumbnail
        color: "white"
        width: UM.Theme.getSize("toolbox_thumbnail_large").width
        height: UM.Theme.getSize("toolbox_thumbnail_large").height
        anchors
        {
            top: parent.top
            horizontalCenter: parent.horizontalCenter
            topMargin: UM.Theme.getSize("default_lining").width
        }
        Image
        {
            anchors.centerIn: parent
            width: UM.Theme.getSize("toolbox_thumbnail_large").width - 2 * UM.Theme.getSize("default_margin").width
            height: UM.Theme.getSize("toolbox_thumbnail_large").height - 2 * UM.Theme.getSize("default_margin").height
            fillMode: Image.PreserveAspectFit
            source: model.icon_url || "../images/logobot.svg"
            mipmap: true
        }
        UM.RecolorImage
        {
            width: (parent.width * 0.3) | 0
            height: (parent.height * 0.3) | 0
            anchors
            {
                bottom: parent.bottom
                right: parent.right
                bottomMargin: UM.Theme.getSize("default_lining").width
            }
            sourceSize.width: width
            sourceSize.height: height
            visible: installedPackages != 0
            color: (installedPackages == packageCount) ? UM.Theme.getColor("primary") : UM.Theme.getColor("border")
            source: "../images/installed_check.svg"
        }
    }
    Rectangle
    {
        id: packageNameBackground
        color: UM.Theme.getColor("primary")
        anchors
        {
            top: thumbnail.bottom
            horizontalCenter: parent.horizontalCenter
        }
        height: UM.Theme.getSize("toolbox_heading_label").height
        width: parent.width
        Label
        {
            id: packageName
            text: model.name
            anchors
            {
                horizontalCenter: parent.horizontalCenter
            }
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            height: UM.Theme.getSize("toolbox_heading_label").height
            width: parent.width
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("button_text")
            font: UM.Theme.getFont("medium_bold")
        }
    }
    MouseArea
    {
        anchors.fill: parent
        hoverEnabled: true
        onEntered:
        {
            packageName.color = UM.Theme.getColor("button_text_hover")
            packageNameBackground.color = UM.Theme.getColor("primary_hover")
            tileBase.border.color = UM.Theme.getColor("primary_hover")
        }
        onExited:
        {
            packageName.color = UM.Theme.getColor("button_text")
            packageNameBackground.color = UM.Theme.getColor("primary")
            tileBase.border.color = UM.Theme.getColor("lining")
        }
        onClicked:
        {
            base.selection = model
            switch(toolbox.viewCategory)
            {
                case "material":

                    // If model has a type, it must be a package
                    if (model.type !== undefined)
                    {
                        toolbox.viewPage = "detail"
                        toolbox.filterModelByProp("packages", "id", model.id)
                    }
                    else
                    {
                        toolbox.viewPage = "author"
                        toolbox.setFilters("packages", {
                            "author_id": model.id,
                            "type": "material"
                        })
                    }
                    break
                default:
                    toolbox.viewPage = "detail"
                    toolbox.filterModelByProp("packages", "id", model.id)
                    break
            }
        }
    }
}
