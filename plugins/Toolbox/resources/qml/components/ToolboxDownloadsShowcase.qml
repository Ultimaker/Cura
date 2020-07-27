// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Rectangle
{
    color: UM.Theme.getColor("secondary")
    height: childrenRect.height
    width: parent.width
    Column
    {
        height: childrenRect.height + 2 * padding
        spacing: UM.Theme.getSize("default_margin").height
        width: parent.width
        padding: UM.Theme.getSize("wide_margin").height
        Item
        {
            width: parent.width - parent.padding * 2
            height: childrenRect.height
            Label
            {
                id: heading
                text: catalog.i18nc("@label", "Premium")
                width: contentWidth
                height: contentHeight
                color: UM.Theme.getColor("text_medium")
                font: UM.Theme.getFont("large")
                renderType: Text.NativeRendering
            }
            UM.TooltipArea
            {
                width: childrenRect.width
                height: childrenRect.height
                anchors.right: parent.right
                text: catalog.i18nc("@info:tooltip", "Go to Web Marketplace")
                Label
                {
                    text: "<a href='%2'>".arg(toolbox.getWebMarketplaceUrl("materials")) + catalog.i18nc("@label", "Search materials") + "</a>"
                    width: contentWidth
                    height: contentHeight
                    horizontalAlignment: Text.AlignRight
                    font: UM.Theme.getFont("default")
                    renderType: Text.NativeRendering

                    linkColor: UM.Theme.getColor("text_link")
                    onLinkActivated: Qt.openUrlExternally(link)

                    visible: toolbox.viewCategory === "material"
                }
            }
        }
        Grid
        {
            height: childrenRect.height
            spacing: UM.Theme.getSize("wide_margin").width
            columns: 3
            anchors.horizontalCenter: parent.horizontalCenter

            Repeater
            {
                model:
                {
                    if (toolbox.viewCategory == "plugin")
                    {
                        return toolbox.pluginsShowcaseModel
                    }
                    if (toolbox.viewCategory == "material")
                    {
                        return toolbox.materialsShowcaseModel
                    }
                }
                delegate: Loader
                {
                    asynchronous: true
                    source: "ToolboxDownloadsShowcaseTile.qml"
                }
            }
        }
    }
}
