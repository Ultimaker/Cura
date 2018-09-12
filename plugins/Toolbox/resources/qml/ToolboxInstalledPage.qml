// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
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
        anchors
        {
            right: parent.right
            left: parent.left
            leftMargin: UM.Theme.getSize("wide_margin").width
            topMargin: UM.Theme.getSize("wide_margin").height
            bottomMargin: UM.Theme.getSize("wide_margin").height
            top: parent.top
        }
        height: childrenRect.height + 4 * UM.Theme.getSize("default_margin").height
        Label
        {
            visible: toolbox.pluginsInstalledModel.items.length > 0
            width: parent.width
            text: catalog.i18nc("@title:tab", "Plugins")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
        }
        Rectangle
        {
            visible: toolbox.pluginsInstalledModel.items.length > 0
            color: "transparent"
            width: parent.width
            height: childrenRect.height + 1 * UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
            Column
            {
                height: childrenRect.height
                anchors
                {
                    top: parent.top
                    right: parent.right
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    rightMargin: UM.Theme.getSize("default_margin").width
                    topMargin: UM.Theme.getSize("default_lining").width
                    bottomMargin: UM.Theme.getSize("default_lining").width
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
            visible: toolbox.materialsInstalledModel.items.length > 0
            width: page.width
            text: catalog.i18nc("@title:tab", "Materials")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
        }
        Rectangle
        {
            visible: toolbox.materialsInstalledModel.items.length > 0
            color: "transparent"
            width: parent.width
            height: childrenRect.height + 1 * UM.Theme.getSize("default_lining").width
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
            Column
            {
                height: Math.max( UM.Theme.getSize("wide_margin").height, childrenRect.height)
                anchors
                {
                    top: parent.top
                    right: parent.right
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    rightMargin: UM.Theme.getSize("default_margin").width
                    topMargin: UM.Theme.getSize("default_lining").width
                    bottomMargin: UM.Theme.getSize("default_lining").width
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
