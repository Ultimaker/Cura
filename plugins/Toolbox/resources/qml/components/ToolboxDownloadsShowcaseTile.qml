// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
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
    height: thumbnail.height + packageName.height + rating.height + UM.Theme.getSize("default_margin").width
    border.width: UM.Theme.getSize("default_lining").width
    border.color: UM.Theme.getColor("lining")
    color: UM.Theme.getColor("main_background")
    Image
    {
        id: thumbnail
        height: UM.Theme.getSize("toolbox_thumbnail_large").height - 4 * UM.Theme.getSize("default_margin").height
        width: UM.Theme.getSize("toolbox_thumbnail_large").height - 4 * UM.Theme.getSize("default_margin").height
        sourceSize.height: height
        sourceSize.width: width
        fillMode: Image.PreserveAspectFit
        source: model.icon_url || "../../images/placeholder.svg"
        mipmap: true
        anchors
        {
            top: parent.top
            topMargin: UM.Theme.getSize("default_margin").height
            horizontalCenter: parent.horizontalCenter
        }
    }
    Label
    {
        id: packageName
        text: model.name
        anchors
        {
            horizontalCenter: parent.horizontalCenter
            top: thumbnail.bottom
        }
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        renderType: Text.NativeRendering
        height: UM.Theme.getSize("toolbox_heading_label").height
        width: parent.width - UM.Theme.getSize("default_margin").width
        wrapMode: Text.WordWrap
        elide: Text.ElideRight
        font: UM.Theme.getFont("medium_bold")
        color: UM.Theme.getColor("text")
    }
    UM.RecolorImage
    {
        width: (parent.width * 0.20) | 0
        height: width
        anchors
        {
            bottom: bottomBorder.top
            right: parent.right
        }
        visible: installedPackages != 0
        color: (installedPackages >= packageCount) ? UM.Theme.getColor("primary") : UM.Theme.getColor("border")
        source: "../../images/installed_check.svg"
    }

    SmallRatingWidget
    {
        id: rating
        anchors.bottom: parent.bottom
        anchors.bottomMargin: UM.Theme.getSize("narrow_margin").height
        anchors.horizontalCenter: parent.horizontalCenter
    }
    Rectangle
    {
        id: bottomBorder
        color: UM.Theme.getColor("primary")
        anchors.bottom: parent.bottom
        width: parent.width
        height: UM.Theme.getSize("toolbox_header_highlight").height
    }

    MouseArea
    {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: tileBase.border.color = UM.Theme.getColor("primary")
        onExited: tileBase.border.color = UM.Theme.getColor("lining")
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
