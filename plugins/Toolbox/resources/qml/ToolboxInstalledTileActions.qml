// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

import Cura 1.1 as Cura

Column
{
    property bool canUpdate: CuraApplication.getPackageManager().packagesWithUpdate.indexOf(model.id) != -1
    property bool canDowngrade: false
    property bool loginRequired: model.login_required && !Cura.API.account.isLoggedIn
    width: UM.Theme.getSize("toolbox_action_button").width
    spacing: UM.Theme.getSize("narrow_margin").height

    Label
    {
        visible: !model.is_installed
        text: catalog.i18nc("@label", "Will install upon restarting")
        color: UM.Theme.getColor("lining")
        font: UM.Theme.getFont("default")
        wrapMode: Text.WordWrap
        width: parent.width
        renderType: Text.NativeRendering
    }

    ToolboxProgressButton
    {
        id: updateButton
        active: toolbox.isDownloading && toolbox.activePackage == model
        readyLabel: catalog.i18nc("@action:button", "Update")
        activeLabel: catalog.i18nc("@action:button", "Updating")
        completeLabel: catalog.i18nc("@action:button", "Updated")
        onReadyAction:
        {
            toolbox.activePackage = model
            toolbox.update(model.id)
        }
        onActiveAction: toolbox.cancelDownload()

        // Don't allow installing while another download is running
        enabled: !(toolbox.isDownloading && toolbox.activePackage != model) && !loginRequired
        opacity: enabled ? 1.0 : 0.5
        visible: canUpdate
    }

    Label
    {
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label:The string between <a href=> and </a> is the highlighted link", "<a href='%1'>Log in</a> is required to update")
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        linkColor: UM.Theme.getColor("text_link")
        visible: loginRequired
        width: updateButton.width
        renderType: Text.NativeRendering

        MouseArea
        {
            anchors.fill: parent
            onClicked: Cura.API.account.login()
        }
    }

    Cura.SecondaryButton
    {
        id: removeButton
        text: canDowngrade ? catalog.i18nc("@action:button", "Downgrade") : catalog.i18nc("@action:button", "Uninstall")
        visible: !model.is_bundled && model.is_installed
        enabled: !toolbox.isDownloading

        width: UM.Theme.getSize("toolbox_action_button").width
        height: UM.Theme.getSize("toolbox_action_button").height

        fixedWidthMode: true

        onClicked: toolbox.checkPackageUsageAndUninstall(model.id)
        Connections
        {
            target: toolbox
            onMetadataChanged:
            {
                canDowngrade = toolbox.canDowngrade(model.id)
            }
        }
    }
}
