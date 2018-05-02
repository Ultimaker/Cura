// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: tile
    property bool installed: toolbox.isInstalled(model.id)
    property var packageData: model
    width: detailList.width - UM.Theme.getSize("wide_margin").width
    height: Math.max(UM.Theme.getSize("toolbox_detail_tile").height, childrenRect.height + UM.Theme.getSize("default_margin").height)
    Item
    {
        id: normalData
        height: childrenRect.height
        anchors
        {
            left: parent.left
            right: controls.left
            rightMargin: UM.Theme.getSize("default_margin").width
            top: parent.top
        }
        Label
        {
            id: packageName
            width: parent.width
            height: UM.Theme.getSize("toolbox_property_label").height
            text: model.name
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("medium_bold")
        }
        Label
        {
            anchors.top: packageName.bottom
            width: parent.width
            text: model.description
            maximumLineCount: 3
            elide: Text.ElideRight
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
        }
    }
    Item
    {
        id: controls
        anchors.right: tile.right
        anchors.top: tile.top
        width: childrenRect.width
        height: childrenRect.height
        Button
        {
            id: installButton
            text:
            {
                if (installed)
                {
                    return catalog.i18nc("@action:button", "Installed")
                }
                else
                {
                    if (toolbox.isDownloading && toolbox.activePackage == model)
                    {
                        return catalog.i18nc("@action:button", "Cancel")
                    }
                    else
                    {
                        return catalog.i18nc("@action:button", "Install")
                    }
                }
            }
            enabled: installed || !(toolbox.isDownloading && toolbox.activePackage != model) //Don't allow installing while another download is running.
            opacity: enabled ? 1.0 : 0.5
            style: ButtonStyle
            {
                background: Rectangle
                {
                    implicitWidth: 96
                    implicitHeight: 30
                    color:
                    {
                        if (installed)
                        {
                            return UM.Theme.getColor("action_button_disabled")
                        }
                        else
                        {
                            if ( control.hovered )
                            {
                                return UM.Theme.getColor("primary_hover")
                            }
                            else
                            {
                                return UM.Theme.getColor("primary")
                            }
                        }

                    }
                }
                label: Label
                {
                    text: control.text
                    color:
                    {
                        if (installed)
                        {
                            return UM.Theme.getColor("action_button_disabled_text")
                        }
                        else
                        {
                            if ( control.hovered )
                            {
                                return UM.Theme.getColor("button_text_hover")
                            }
                            else
                            {
                                return UM.Theme.getColor("button_text")
                            }
                        }
                    }
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font: UM.Theme.getFont("default_bold")
                }
            }
            onClicked:
            {
                if (installed)
                {
                    toolbox.viewCategory = "installed"
                }
                else
                {
                    // if ( toolbox.isDownloading && toolbox.activePackage == model )
                    if ( toolbox.isDownloading )
                    {
                        toolbox.cancelDownload();
                    }
                    else
                    {
                        toolbox.activePackage = model
                        // toolbox.activePackage = model;
                        if ( model.can_upgrade )
                        {
                            // toolbox.downloadAndInstallPlugin( model.update_url );
                        }
                        else
                        {
                            toolbox.startDownload( model.download_url );
                        }
                    }
                }
            }
        }
    }

    ToolboxCompatibilityChart
    {
        id: compatibilityChart
        anchors.top: normalData.bottom
        width: normalData.width
    }

    Rectangle
    {
        color: UM.Theme.getColor("lining")
        width: tile.width
        height: UM.Theme.getSize("default_lining").height
        anchors.top: compatibilityChart.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height + UM.Theme.getSize("wide_margin").height //Normal margin for spacing after chart, wide margin between items.
    }
    Connections
    {
        target: toolbox
        onInstallChanged: installed = toolbox.isInstalled(model.id)
    }
}
