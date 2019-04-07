// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: tile
    width: detailList.width - UM.Theme.getSize("wide_margin").width
    height: normalData.height + compatibilityChart.height + 4 * UM.Theme.getSize("default_margin").height
    Item
    {
        id: normalData
        height: childrenRect.height
        anchors
        {
            left: parent.left
            right: controls.left
            rightMargin: UM.Theme.getSize("default_margin").width * 2 + UM.Theme.getSize("toolbox_loader").width
            top: parent.top
        }
        Label
        {
            id: packageName
            width: parent.width
            height: UM.Theme.getSize("toolbox_property_label").height
            text: model.name
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("medium_bold")
            renderType: Text.NativeRendering
        }
        Label
        {
            anchors.top: packageName.bottom
            width: parent.width
            text: model.description
            maximumLineCount: 25
            elide: Text.ElideRight
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
        }
    }

    ToolboxDetailTileActions
    {
        id: controls
        anchors.right: tile.right
        anchors.top: tile.top
        width: childrenRect.width
        height: childrenRect.height
        packageData: model
    }

    ToolboxCompatibilityChart
    {
        id: compatibilityChart
        anchors.top: normalData.bottom
        width: normalData.width
        packageData: model
    }

    Rectangle
    {
        color: UM.Theme.getColor("lining")
        width: tile.width
        height: UM.Theme.getSize("default_lining").height
        anchors.top: compatibilityChart.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height + UM.Theme.getSize("wide_margin").height //Normal margin for spacing after chart, wide margin between items.
    }
}
