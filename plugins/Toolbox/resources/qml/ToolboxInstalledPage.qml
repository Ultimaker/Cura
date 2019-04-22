// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.1 as UM

ScrollView
{
    id: page
    frameVisible: false
    width: parent.width
    height: parent.height
    style: UM.Theme.styles.scrollview
    flickableItem.flickableDirection: Flickable.VerticalFlick

    Column
    {
        spacing: UM.Theme.getSize("default_margin").height
        visible: toolbox.pluginsInstalledModel.items.length > 0
        height: childrenRect.height + 4 * UM.Theme.getSize("default_margin").height

        anchors
        {
            right: parent.right
            left: parent.left
            margins: UM.Theme.getSize("default_margin").width
            top: parent.top
        }

        Label
        {
            width: page.width
            text: catalog.i18nc("@title:tab", "Plugins")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("large")
            renderType: Text.NativeRendering
        }
        Rectangle
        {
            id: installedPlugins
            color: "transparent"
            width: parent.width
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
            Column
            {
                anchors
                {
                    top: parent.top
                    right: parent.right
                    left: parent.left
                    margins: UM.Theme.getSize("default_margin").width
                }
                Repeater
                {
                    id: materialList
                    model: toolbox.pluginsInstalledModel
                    delegate: ToolboxInstalledTile {}
                }
            }
        }
        Label
        {
            text: catalog.i18nc("@title:tab", "Materials")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
        }

        Rectangle
        {
            id: installedMaterials
            color: "transparent"
            width: parent.width
            height: childrenRect.height + UM.Theme.getSize("default_margin").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
            Column
            {
                anchors
                {
                    top: parent.top
                    right: parent.right
                    left: parent.left
                    margins: UM.Theme.getSize("default_margin").width
                }
                Repeater
                {
                    id: pluginList
                    model: toolbox.materialsInstalledModel
                    delegate: ToolboxInstalledTile {}
                }
            }
        }
    }
}
