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
        spacing: UM.Theme.getSize("toolbox_showcase_spacing").width
        width: parent.width
        padding: UM.Theme.getSize("wide_margin").height
        Label
        {
            id: heading
            text: catalog.i18nc("@label", "Featured")
            width: parent.width
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("large")
            renderType: Text.NativeRendering
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
