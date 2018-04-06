// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Rectangle
{
    width: base.width
    height: UM.Theme.getSize("base_unit").height * 12
    color: "steelblue"
    Column
    {
        anchors
        {
            left: parent.left
            right: controls.left
            rightMargin: UM.Theme.getSize("default_margin").width
            top: parent.top
            leftMargin: UM.Theme.getSize("default_margin").width
            topMargin: UM.Theme.getSize("default_margin").height
        }
        Label
        {
            width: parent.width
            height: UM.Theme.getSize("base_unit").height * 2
            text: model.name
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default_bold")
        }
        Label
        {
            width: parent.width
            text: model.description
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text")
            font: UM.Theme.getFont("default")
        }
    }
    Rectangle
    {
        id: controls
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: childrenRect.width
        Button {
            id: installButton
            text: catalog.i18nc("@action:button", "Install")
            enabled:
            {
                if ( manager.isDownloading )
                {
                    return pluginList.activePlugin == model ? true : false
                }
                else
                {
                    return true
                }
            }
            opacity: enabled ? 1.0 : 0.5
            style: ButtonStyle {
                background: Rectangle
                {
                    implicitWidth: 96
                    implicitHeight: 30
                    color: UM.Theme.getColor("primary")
                }
                label: Label
                {
                    text: control.text
                    color: "white"
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            onClicked:
            {
                if ( manager.isDownloading && pluginList.activePlugin == model )
                {
                    manager.cancelDownload();
                }
                else
                {
                    pluginList.activePlugin = model;
                    if ( model.can_upgrade )
                    {
                        manager.downloadAndInstallPlugin( model.update_url );
                    }
                    else {
                        manager.downloadAndInstallPlugin( model.file_location );
                    }
                }
            }
        }
    }
    Rectangle
    {
        color: UM.Theme.getColor("text_medium")
        width: parent.width
        height: UM.Theme.getSize("default_lining").height
        anchors.top: parent.top
    }
}
