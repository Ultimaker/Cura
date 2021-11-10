// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import UM 1.5 as UM

Item
{
    height: UM.Theme.getSize("toolbox_installed_tile").height
    width: parent.width
    property bool isEnabled: true

    Rectangle
    {
        color: UM.Theme.getColor("lining")
        width: parent.width
        height: Math.floor(UM.Theme.getSize("default_lining").height)
        anchors.bottom: parent.top
        visible: index != 0
    }
    Row
    {
        id: tileRow
        height: parent.height
        width: parent.width
        spacing: UM.Theme.getSize("default_margin").width
        topPadding: UM.Theme.getSize("default_margin").height

        UM.CheckBox
        {
            id: disableButton
            anchors.verticalCenter: pluginInfo.verticalCenter
            checked: isEnabled
            visible: model.type == "plugin"
            width: visible ? UM.Theme.getSize("checkbox").width : 0
            enabled: !toolbox.isDownloading
            onClicked: toolbox.isEnabled(model.id) ? toolbox.disable(model.id) : toolbox.enable(model.id)
        }
        Column
        {
            id: pluginInfo
            topPadding: UM.Theme.getSize("narrow_margin").height
            property var color: model.type === "plugin" && !isEnabled ? UM.Theme.getColor("lining") : UM.Theme.getColor("text")
            width: Math.floor(tileRow.width - (authorInfo.width + pluginActions.width + 2 * tileRow.spacing + ((disableButton.visible) ? disableButton.width + tileRow.spacing : 0)))
            UM.Label
            {
                text: model.name
                width: parent.width
                maximumLineCount: 1
                elide: Text.ElideRight
                wrapMode: Text.WordWrap
                font: UM.Theme.getFont("large_bold")
                color: pluginInfo.color
            }
            UM.Label
            {
                text: model.description
                font: UM.Theme.getFont("default")
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
            width: Math.floor(UM.Theme.getSize("toolbox_action_button").width * 1.25)

            UM.Label
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
                font: UM.Theme.getFont("medium")
                width: parent.width
                height: Math.floor(UM.Theme.getSize("toolbox_property_label").height)
                wrapMode: Text.WordWrap

                horizontalAlignment: Text.AlignLeft
                onLinkActivated: Qt.openUrlExternally("mailto:" + model.author_email + "?Subject=Cura: " + model.name + " Plugin")
                color: model.enabled ? UM.Theme.getColor("text") : UM.Theme.getColor("lining")
            }

            UM.Label
            {
                text: model.version
                width: parent.width
                height: UM.Theme.getSize("toolbox_property_label").height
                horizontalAlignment: Text.AlignLeft
            }
        }
        ToolboxInstalledTileActions
        {
            id: pluginActions
        }
        Connections
        {
            target: toolbox
            function onToolboxEnabledChanged() { isEnabled = toolbox.isEnabled(model.id) }
        }
    }
}
