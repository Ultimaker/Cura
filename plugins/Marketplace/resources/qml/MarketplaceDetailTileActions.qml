// Copyright (c) 2018 Ultimaker B.V.
// Marketplace is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Column
{
    property bool installed: marketplace.isInstalled(model.id)
    property bool canUpdate: marketplace.canUpdate(model.id)
    width: UM.Theme.getSize("marketplace_action_button").width
    spacing: UM.Theme.getSize("narrow_margin").height

    MarketplaceProgressButton
    {
        id: installButton
        active: marketplace.isDownloading && marketplace.activePackage == model
        complete: installed
        readyAction: function()
        {
            marketplace.activePackage = model
            marketplace.startDownload(model.download_url)
        }
        activeAction: function()
        {
            marketplace.cancelDownload()
        }
        completeAction: function()
        {
            marketplace.viewCategory = "installed"
        }
        // Don't allow installing while another download is running
        enabled: installed || !(marketplace.isDownloading && marketplace.activePackage != model)
        opacity: enabled ? 1.0 : 0.5
        visible: !updateButton.visible // Don't show when the update button is visible
    }

    MarketplaceProgressButton
    {
        id: updateButton
        active: marketplace.isDownloading && marketplace.activePackage == model
        readyLabel: catalog.i18nc("@action:button", "Update")
        activeLabel: catalog.i18nc("@action:button", "Updating")
        completeLabel: catalog.i18nc("@action:button", "Updated")
        readyAction: function()
        {
            marketplace.activePackage = model
            marketplace.update(model.id)
        }
        activeAction: function()
        {
            marketplace.cancelDownload()
        }
        // Don't allow installing while another download is running
        enabled: !(marketplace.isDownloading && marketplace.activePackage != model)
        opacity: enabled ? 1.0 : 0.5
        visible: canUpdate
    }
    Connections
    {
        target: marketplace
        onInstallChanged: installed = marketplace.isInstalled(model.id)
        onMetadataChanged: canUpdate = marketplace.canUpdate(model.id)
    }
}
