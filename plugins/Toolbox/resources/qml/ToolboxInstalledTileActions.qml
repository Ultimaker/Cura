// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Column
{
    property bool canUpdate: false
    property bool canDowngrade: false
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

    Button
    {
        id: removeButton
        text: canDowngrade ? catalog.i18nc("@action:button", "Downgrade") : catalog.i18nc("@action:button", "Uninstall")
        visible: !model.is_bundled && model.is_installed
        enabled: !toolbox.isDownloading
        style: ButtonStyle
        {
            background: Rectangle
            {
                implicitWidth: UM.Theme.getSize("toolbox_action_button").width
                implicitHeight: UM.Theme.getSize("toolbox_action_button").height
                color: "transparent"
                border
                {
                    width: UM.Theme.getSize("default_lining").width
                    color:
                    {
                        if (control.hovered)
                        {
                            return UM.Theme.getColor("primary_hover")
                        }
                        else
                        {
                            return UM.Theme.getColor("lining")
                        }
                    }
                }
            }
            label: Label
            {
                text: control.text
                color: UM.Theme.getColor("text")
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                font: UM.Theme.getFont("default")
            }
        }
        onClicked: toolbox.checkPackageUsageAndUninstall(model.id)
        Connections
        {
            target: toolbox
            onMetadataChanged:
            {
                canUpdate = toolbox.canUpdate(model.id)
                canDowngrade = toolbox.canDowngrade(model.id)
            }
        }
    }
}
