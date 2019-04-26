// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3
import UM 1.1 as UM
import Cura 1.1 as Cura

Item
{
    id: toolboxDownloadsGridTile
    property int packageCount: (toolbox.viewCategory == "material" && model.type === undefined) ? toolbox.getTotalNumberOfMaterialPackagesByAuthor(model.id) : 1
    property int installedPackages: (toolbox.viewCategory == "material" && model.type === undefined) ? toolbox.getNumberOfInstalledPackagesByAuthor(model.id) : (toolbox.isInstalled(model.id) ? 1 : 0)
    height: childrenRect.height
    Layout.alignment: Qt.AlignTop | Qt.AlignLeft

    MouseArea
    {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: thumbnail.border.color = UM.Theme.getColor("primary")
        onExited: thumbnail.border.color = UM.Theme.getColor("lining")
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

    Rectangle
    {
        id: thumbnail
        width: UM.Theme.getSize("toolbox_thumbnail_small").width
        height: UM.Theme.getSize("toolbox_thumbnail_small").height
        color: UM.Theme.getColor("main_background")
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")

        Image
        {
            anchors.centerIn: parent
            width: UM.Theme.getSize("toolbox_thumbnail_small").width - UM.Theme.getSize("wide_margin").width
            height: UM.Theme.getSize("toolbox_thumbnail_small").height - UM.Theme.getSize("wide_margin").width
            fillMode: Image.PreserveAspectFit
            source: model.icon_url || "../images/logobot.svg"
            mipmap: true
        }
        UM.RecolorImage
        {
            width: (parent.width * 0.4) | 0
            height: (parent.height * 0.4) | 0
            anchors
            {
                bottom: parent.bottom
                right: parent.right
            }
            sourceSize.height: height
            visible: installedPackages != 0
            color: (installedPackages >= packageCount) ? UM.Theme.getColor("primary") : UM.Theme.getColor("border")
            source: "../images/installed_check.svg"
        }
    }
    Item
    {
        anchors
        {
            left: thumbnail.right
            leftMargin: Math.floor(UM.Theme.getSize("narrow_margin").width)
            right: parent.right
            top: parent.top
            bottom: parent.bottom
        }

        Label
        {
            id: name
            text: model.name
            width: parent.width
            elide: Text.ElideRight
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default_bold")
        }
        Label
        {
            id: info
            text: model.description
            elide: Text.ElideRight
            width: parent.width
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
            anchors.top: name.bottom
            anchors.bottom: rating.top
            verticalAlignment: Text.AlignVCenter
            maximumLineCount: 2
        }
        SmallRatingWidget
        {
            id: rating
            anchors
            {
                bottom: parent.bottom
                left: parent.left
                right: parent.right
            }
        }
    }
}
