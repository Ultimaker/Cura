// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import UM 1.1 as UM

Item
{
    id: header
    width: parent.width
    height: UM.Theme.getSize("toolbox_header").height
    Row
    {
        id: bar
        spacing: UM.Theme.getSize("default_margin").width
        height: childrenRect.height
        width: childrenRect.width
        anchors
        {
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
        }

        ToolboxTabButton
        {
            id: pluginsTabButton
            text: catalog.i18nc("@title:tab", "Plugins")
            active: toolbox.viewCategory == "plugin" && enabled
            enabled: !toolbox.isDownloading && toolbox.viewPage != "loading" && toolbox.viewPage != "errored"
            onClicked:
            {
                toolbox.filterModelByProp("packages", "type", "plugin")
                toolbox.viewCategory = "plugin"
                toolbox.viewPage = "overview"
            }
        }

        ToolboxTabButton
        {
            id: materialsTabButton
            text: catalog.i18nc("@title:tab", "Materials")
            active: toolbox.viewCategory == "material" && enabled
            enabled: !toolbox.isDownloading && toolbox.viewPage != "loading" && toolbox.viewPage != "errored"
            onClicked:
            {
                toolbox.filterModelByProp("authors", "package_types", "material")
                toolbox.viewCategory = "material"
                toolbox.viewPage = "overview"
            }
        }
    }
    ToolboxTabButton
    {
        id: installedTabButton
        text: catalog.i18nc("@title:tab", "Installed")
        active: toolbox.viewCategory == "installed"
        enabled: !toolbox.isDownloading
        anchors
        {
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
        }
        onClicked: toolbox.viewCategory = "installed"
    }
    ToolboxShadow
    {
        anchors.top: bar.bottom
    }
}
