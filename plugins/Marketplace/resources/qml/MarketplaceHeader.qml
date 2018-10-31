// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import UM 1.1 as UM

Item
{
    id: header
    width: parent.width
    height: UM.Theme.getSize("marketplace_header").height
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

        MarketplaceTabButton
        {
            id: pluginsTabButton
            text: catalog.i18nc("@title:tab", "Plugins")
            active: marketplace.viewCategory == "plugin" && enabled
            enabled: !marketplace.isDownloading && marketplace.viewPage != "loading" && marketplace.viewPage != "errored"
            onClicked:
            {
                marketplace.filterModelByProp("packages", "type", "plugin")
                marketplace.viewCategory = "plugin"
                marketplace.viewPage = "overview"
            }
        }

        MarketplaceTabButton
        {
            id: materialsTabButton
            text: catalog.i18nc("@title:tab", "Materials")
            active: marketplace.viewCategory == "material" && enabled
            enabled: !marketplace.isDownloading && marketplace.viewPage != "loading" && marketplace.viewPage != "errored"
            onClicked:
            {
                marketplace.filterModelByProp("authors", "package_types", "material")
                marketplace.viewCategory = "material"
                marketplace.viewPage = "overview"
            }
        }
    }
    MarketplaceTabButton
    {
        id: installedTabButton
        text: catalog.i18nc("@title:tab", "Installed")
        active: marketplace.viewCategory == "installed"
        enabled: !marketplace.isDownloading
        anchors
        {
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
        }
        onClicked: marketplace.viewCategory = "installed"
    }
    MarketplaceShadow
    {
        anchors.top: bar.bottom
    }
}
