// Copyright (c) 2020 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4

import UM 1.4 as UM
import Cura 1.0 as Cura

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

        ToolboxTabButton
        {
            id: installedTabButton
            text: catalog.i18nc("@title:tab", "Installed")
            active: toolbox.viewCategory == "installed"
            enabled: !toolbox.isDownloading
            onClicked: toolbox.viewCategory = "installed"
            width: UM.Theme.getSize("toolbox_header_tab").width + marketplaceNotificationIcon.width - UM.Theme.getSize("default_margin").width
        }


    }

    Cura.NotificationIcon
    {
        id: marketplaceNotificationIcon
        visible: CuraApplication.getPackageManager().packagesWithUpdate.length > 0
        anchors.right: bar.right
        labelText:
        {
            const itemCount = CuraApplication.getPackageManager().packagesWithUpdate.length
            return itemCount > 9 ? "9+" : itemCount
        }
    }


    UM.TooltipArea
    {
        width: childrenRect.width;
        height: parent.height
        text: catalog.i18nc("@info:tooltip", "Go to Web Marketplace")
        anchors
        {
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
            verticalCenter: parent.verticalCenter
        }
        Image
        {
            id: cloudMarketplaceButton
            source: "../../images/shop.svg"
            height: parent.height / 2
            width: height
            anchors.verticalCenter: parent.verticalCenter
            sourceSize.width: width
            sourceSize.height: height
            fillMode: Image.PreserveAspectFit
            MouseArea
            {
                anchors.fill: parent
                onClicked: Qt.openUrlExternally(toolbox.getWebMarketplaceUrl)
            }
        }
    }

    ToolboxShadow
    {
        anchors.top: bar.bottom
    }
}
