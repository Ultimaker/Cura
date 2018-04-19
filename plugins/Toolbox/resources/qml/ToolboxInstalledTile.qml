// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: base
    property bool canUpdate: false
    property bool isEnabled: true
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
        property var color: isEnabled ? UM.Theme.getColor("text") : UM.Theme.getColor("lining")
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
            height: UM.Theme.getSize("base_unit").height * 2
            wrapMode: Text.WordWrap
            verticalAlignment: Text.AlignVCenter
            font: UM.Theme.getFont("default_bold")
            color: pluginInfo.color
        }
        Text
        {
            text: model.description
            width: parent.width
            height: UM.Theme.getSize("base_unit").height * 3
            clip: true
            wrapMode: Text.WordWrap
            color: pluginInfo.color
            elide: Text.ElideRight
        }
    }
    Column
    {
        id: authorInfo
        width: UM.Theme.getSize("base_unit").width * 16
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
            text:
            {
                if (model.author_email)
                {
                    return "<a href=\"mailto:"+model.author_email+"?Subject=Cura: "+model.name+"\">"+model.author_name+"</a>"
                }
                else
                {
                    return model.author_name
                }
            }
            width: parent.width
            height: UM.Theme.getSize("base_unit").height * 3
            wrapMode: Text.WordWrap
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignLeft
            onLinkActivated: Qt.openUrlExternally("mailto:"+model.author_email+"?Subject=Cura: "+model.name+" Plugin")
            color: model.enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("lining")
        }
    }
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
            text:
            {
                if (model.is_bundled)
                {
                    return isEnabled ? catalog.i18nc("@action:button", "Disable") : catalog.i18nc("@action:button", "Enable")
                }
                else
                {
                    return catalog.i18nc("@action:button", "Uninstall")
                }
            }
            enabled: !toolbox.isDownloading
            style: ButtonStyle
            {
                background: Rectangle
                {
                    implicitWidth: UM.Theme.getSize("base_unit").width * 8
                    implicitHeight: Math.floor(UM.Theme.getSize("base_unit").width * 2.5)
                    color: "transparent"
                    border
                    {
                        width: UM.Theme.getSize("default_lining").width
                        color: UM.Theme.getColor("lining")
                    }
                }
                label: Text
                {
                    text: control.text
                    color: UM.Theme.getColor("text")
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            onClicked:
            {
                if (model.is_bundled)
                {
                    if (toolbox.isEnabled(model.id))
                    {
                        toolbox.disable(model.id)
                    }
                    else
                    {
                        toolbox.enable(model.id)
                    }
                }
                else
                {
                    toolbox.uninstall( model.id )
                }
            }
        }
        Button
        {
            id: updateButton
            text: catalog.i18nc("@action:button", "Update")
            visible: canUpdate
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
                toolbox.update(model.id);
            }
        }
        ProgressBar
        {
            id: progressbar
            anchors
            {
                left: updateButton.left
                right: updateButton.right
                top: updateButton.bottom
                topMargin: Math.floor(UM.Theme.getSize("base_unit") / 4)
            }
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
    Connections
    {
        target: toolbox
        onEnabledChanged: isEnabled = toolbox.isEnabled(model.id)
        onMetadataChanged: canUpdate = toolbox.canUpdate(model.id)
    }
}
