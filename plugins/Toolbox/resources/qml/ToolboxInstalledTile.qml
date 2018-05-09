// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    property bool canUpdate: false
    property bool isEnabled: true
    height: UM.Theme.getSize("toolbox_installed_tile").height
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
        property var color: model.type === "plugin" && !isEnabled ? UM.Theme.getColor("lining") : UM.Theme.getColor("text")
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
            height: UM.Theme.getSize("toolbox_property_label").height
            wrapMode: Text.WordWrap
            verticalAlignment: Text.AlignVCenter
            font: UM.Theme.getFont("default_bold")
            color: pluginInfo.color
        }
        Text
        {
            text: model.description
            maximumLineCount: 3
            elide: Text.ElideRight
            width: parent.width
            wrapMode: Text.WordWrap
            color: pluginInfo.color
        }
    }
    Column
    {
        id: authorInfo
        height: parent.height
        width: Math.floor(UM.Theme.getSize("toolbox_action_button").width * 1.25)
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
                    return "<a href=\"mailto:" + model.author_email + "?Subject=Cura: " + model.name + "\">" + model.author_name + "</a>"
                }
                else
                {
                    return model.author_name
                }
            }
            width: parent.width
            height: UM.Theme.getSize("toolbox_property_label").height
            wrapMode: Text.WordWrap
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignLeft
            onLinkActivated: Qt.openUrlExternally("mailto:" + model.author_email + "?Subject=Cura: " + model.name + " Plugin")
            color: model.enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("lining")
            linkColor: UM.Theme.getColor("text_link")
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
        Button
        {
            id: disableButton
            text: isEnabled ? catalog.i18nc("@action:button", "Disable") : catalog.i18nc("@action:button", "Enable")
            visible: model.type == "plugin"
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
                        color: UM.Theme.getColor("lining")
                    }
                }
                label: Label
                {
                    text: control.text
                    color: UM.Theme.getColor("text")
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            onClicked: toolbox.isEnabled(model.id) ? toolbox.disable(model.id) : toolbox.enable(model.id)
        }
        Button
        {
            id: removeButton
            text: catalog.i18nc("@action:button", "Uninstall")
            visible: !model.is_bundled
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
                        color: UM.Theme.getColor("lining")
                    }
                }
                label: Label
                {
                    text: control.text
                    color: UM.Theme.getColor("text")
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                }
            }
            onClicked: toolbox.uninstall(model.id)
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
                    implicitWidth: UM.Theme.getSize("toolbox_action_button").width
                    implicitHeight: UM.Theme.getSize("toolbox_action_button").height
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
            onClicked: toolbox.update(model.id)
        }
        ProgressBar
        {
            id: progressbar
            anchors
            {
                left: updateButton.left
                right: updateButton.right
                top: updateButton.bottom
                topMargin: Math.floor(UM.Theme.getSize("default_margin") / 4)
            }
            value: toolbox.isDownloading ? toolbox.downloadProgress : 0
            visible: toolbox.isDownloading
            style: ProgressBarStyle
            {
                background: Rectangle
                {
                    color: UM.Theme.getColor("lining")
                    implicitHeight: Math.floor(UM.Theme.getSize("toolbox_progress_bar").height)
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
