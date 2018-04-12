// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Rectangle
{
    width: base.width - UM.Theme.getSize("double_margin").width
    height: UM.Theme.getSize("base_unit").height * 8
    color: "transparent"
    Column
    {
        anchors
        {
            left: parent.left
            right: controls.left
            rightMargin: UM.Theme.getSize("default_margin").width
            top: parent.top
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
        width: childrenRect.width
        Button {
            id: installButton
            text: {
                if ( toolbox.isDownloading && toolbox.activePackage == model )
                {
                    return catalog.i18nc("@action:button", "Cancel")
                }
                else
                {
                    return catalog.i18nc("@action:button", "Install")
                }
            }
            enabled:
            {
                if ( toolbox.isDownloading )
                {
                    return toolbox.activePackage == model ? true : false
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
                    color: control.hovered ? UM.Theme.getColor("primary_hover") : UM.Theme.getColor("primary")
                }
                label: Label
                {
                    text: control.text
                    color: control.hovered ? UM.Theme.getColor("button_text") : UM.Theme.getColor("button_text_hover")
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    font: UM.Theme.getFont("default_bold")
                }
            }
            onClicked:
            {
                console.log( "MODEL", model.id )
                toolbox.activePackage = model
                // if ( toolbox.isDownloading && toolbox.activePackage == model )
                if ( toolbox.isDownloading )
                {
                    toolbox.cancelDownload();
                }
                else
                {
                    // toolbox.activePackage = model;
                    if ( model.can_upgrade )
                    {
                        // toolbox.downloadAndInstallPlugin( model.update_url );
                    }
                    else {
                        toolbox.startDownload( model.download_url );
                    }
                }
            }
        }
    }
    Rectangle
    {
        color: UM.Theme.getColor("lining")
        width: parent.width
        height: UM.Theme.getSize("default_lining").height
        anchors.bottom: parent.bottom
    }
}
