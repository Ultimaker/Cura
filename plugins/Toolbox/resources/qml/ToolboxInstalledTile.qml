// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: base
    height: UM.Theme.getSize("base_unit").height * 8
    anchors
    {
        left: parent.left
        right: parent.right
    }
    Rectangle
    {
        color: UM.Theme.getColor("lining")
        width: parent.width
        height: UM.Theme.getSize("default_lining").height
        anchors.bottom: parent.bottom
    }
    Column
    {
        id: pluginInfo
        property var color: model.enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("lining")
        height: parent.height
        anchors
        {
            left: parent.left
            top: parent.top
            right: authorInfo.left
            topMargin: UM.Theme.getSize("default_margin").height
            rightMargin: UM.Theme.getSize("default_margin").width
        }
        Label
        {
            text: model.name
            width: parent.width
            height: 24
            wrapMode: Text.WordWrap
            verticalAlignment: Text.AlignVCenter
            font {
                pixelSize: 13
                bold: true
            }
            color: pluginInfo.color
        }
        Text
        {
            text: model.description
            width: parent.width
            height: 36
            clip: true
            wrapMode: Text.WordWrap
            color: pluginInfo.color
            elide: Text.ElideRight
        }
    }
    Column
    {
        id: authorInfo
        width: 192
        height: parent.height
        anchors
        {
            top: parent.top
            topMargin: UM.Theme.getSize("default_margin").height
            right: pluginActions.left
            rightMargin: UM.Theme.getSize("default_margin").width
        }
        Label
        {
            text: "<a href=\"mailto:"+model.author_email+"?Subject=Cura: "+model.name+"\">"+model.author+"</a>"
            width: parent.width
            height: 24
            wrapMode: Text.WordWrap
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignLeft
            onLinkActivated: Qt.openUrlExternally("mailto:"+model.author_email+"?Subject=Cura: "+model.name+" Plugin")
            color: model.enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("lining")
        }
    }

    // Plugin actions
    Column
    {
        id: pluginActions
        width: childrenRect.width
        height: childrenRect.height
        spacing: UM.Theme.getSize("default_margin").height
        anchors
        {
            top: parent.top
            right: parent.right
            topMargin: UM.Theme.getSize("default_margin").height
        }

        Button {
            id: removeButton
            text: "Uninstall"
            visible: model.can_uninstall && model.status == "installed"
            enabled: !toolbox.isDownloading
            style: ButtonStyle
            {
                background: Rectangle
                {
                    implicitWidth: UM.Theme.getSize("base_unit").width * 8
                    implicitHeight: UM.Theme.getSize("base_unit").width * 2.5
                    color: "transparent"
                    border
                    {
                        width: UM.Theme.getSize("default_lining").width
                        color: UM.Theme.getColor("lining")
                    }
                }
                label: Text {
                    text: control.text
                    color: UM.Theme.getColor("text")
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            onClicked: toolbox.removePlugin( model.id )
        }

        Button {
            id: updateButton
            text: "Update"
            enabled: model.can_update
            style: ButtonStyle
            {
                background: Rectangle
                {
                    implicitWidth: UM.Theme.getSize("base_unit").width * 8
                    implicitHeight: UM.Theme.getSize("base_unit").width * 2.5
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
                toolbox.updatePackage(model.id);
            }
        }
        ProgressBar
        {
            id: progressbar
            anchors.left: installButton.left
            anchors.right: installButton.right
            anchors.top: installButton.bottom
            anchors.topMargin: 4
            value: toolbox.isDownloading ? toolbox.downloadProgress : 0
            visible: toolbox.isDownloading
            style: ProgressBarStyle
            {
                background: Rectangle
                {
                    color: UM.Theme.getColor("lining")
                    implicitHeight: Math.floor(UM.Theme.getSize("base_unit").height / 2)
                }
                progress: Rectangle
                {
                    color: UM.Theme.getColor("primary")
                }
            }
        }
    }
}
