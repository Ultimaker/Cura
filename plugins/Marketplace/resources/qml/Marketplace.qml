// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import UM 1.1 as UM

Window
{
    id: base
    property var selection: null
    title: catalog.i18nc("@title", "Marketplace")
    modality: Qt.ApplicationModal
    flags: Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowCloseButtonHint

    width: 720 * screenScaleFactor
    height: 640 * screenScaleFactor
    minimumWidth: width
    maximumWidth: minimumWidth
    minimumHeight: height
    maximumHeight: minimumHeight
    color: UM.Theme.getColor("sidebar")
    UM.I18nCatalog
    {
        id: catalog
        name:"cura"
    }
    Item
    {
        anchors.fill: parent
        MarketplaceHeader
        {
            id: header
        }

        Item
        {
            id: mainView
            width: parent.width
            z: -1
            anchors
            {
                top: header.bottom
                bottom: footer.top
            }
            // TODO: This could be improved using viewFilter instead of viewCategory
            MarketplaceLoadingPage
            {
                id: viewLoading
                visible: marketplace.viewCategory != "installed" && marketplace.viewPage == "loading"
            }
            MarketplaceErrorPage
            {
                id: viewErrored
                visible: marketplace.viewCategory != "installed" && marketplace.viewPage == "errored"
            }
            MarketplaceDownloadsPage
            {
                id: viewDownloads
                visible: marketplace.viewCategory != "installed" && marketplace.viewPage == "overview"
            }
            MarketplaceDetailPage
            {
                id: viewDetail
                visible: marketplace.viewCategory != "installed" && marketplace.viewPage == "detail"
            }
            MarketplaceAuthorPage
            {
                id: viewAuthor
                visible: marketplace.viewCategory != "installed" && marketplace.viewPage == "author"
            }
            MarketplaceInstalledPage
            {
                id: installedPluginList
                visible: marketplace.viewCategory == "installed"
            }
        }

        MarketplaceFooter
        {
            id: footer
            visible: marketplace.restartRequired
            height: visible ? UM.Theme.getSize("marketplace_footer").height : 0
        }
        // TODO: Clean this up:
        Connections
        {
            target: marketplace
            onShowLicenseDialog:
            {
                licenseDialog.pluginName = marketplace.getLicenseDialogPluginName();
                licenseDialog.licenseContent = marketplace.getLicenseDialogLicenseContent();
                licenseDialog.pluginFileLocation = marketplace.getLicenseDialogPluginFileLocation();
                licenseDialog.show();
            }
        }
        MarketplaceLicenseDialog
        {
            id: licenseDialog
        }
    }
}
