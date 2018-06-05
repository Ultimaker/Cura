// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Column
{
    property bool installed: toolbox.isInstalled(model.id)
    property bool canUpdate: toolbox.canUpdate(model.id)
    width: UM.Theme.getSize("toolbox_action_button").width
    spacing: UM.Theme.getSize("narrow_margin").height

    ToolboxProgressButton
    {
        id: installButton
        active: toolbox.isDownloading && toolbox.activePackage == model
        complete: installed
        readyAction: function()
        {
            toolbox.activePackage = model
            toolbox.startDownload(model.download_url)
        }
        activeAction: function()
        {
            toolbox.cancelDownload()
        }
        completeAction: function()
        {
            toolbox.viewCategory = "installed"
        }
        // Don't allow installing while another download is running
        enabled: installed || !(toolbox.isDownloading && toolbox.activePackage != model)
        opacity: enabled ? 1.0 : 0.5
        visible: !updateButton.visible // Don't show when the update button is visible
    }

    ToolboxProgressButton
    {
        id: updateButton
        active: toolbox.isDownloading && toolbox.activePackage == model
        readyLabel: catalog.i18nc("@action:button", "Update")
        activeLabel: catalog.i18nc("@action:button", "Updating")
        completeLabel: catalog.i18nc("@action:button", "Updated")
        readyAction: function()
        {
            toolbox.activePackage = model
            toolbox.update(model.id)
        }
        activeAction: function()
        {
            toolbox.cancelDownload()
        }
        // Don't allow installing while another download is running
        enabled: !(toolbox.isDownloading && toolbox.activePackage != model)
        opacity: enabled ? 1.0 : 0.5
        visible: canUpdate
    }
    Connections
    {
        target: toolbox
        onInstallChanged: installed = toolbox.isInstalled(model.id)
        onMetadataChanged: canUpdate = toolbox.canUpdate(model.id)
    }
}
