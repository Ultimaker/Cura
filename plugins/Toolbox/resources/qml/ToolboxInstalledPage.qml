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
    id: base
    frameVisible: false
    width: parent.width
    height: parent.height
    style: UM.Theme.styles.scrollview
    Column
    {
        spacing: UM.Theme.getSize("default_margin").height
        anchors
        {
            right: parent.right
            left: parent.left
            leftMargin: UM.Theme.getSize("double_margin").width
            topMargin: UM.Theme.getSize("double_margin").height
            bottomMargin: UM.Theme.getSize("double_margin").height
            top: parent.top
        }
        height: childrenRect.height + 4 * UM.Theme.getSize("default_margin").height
        Label
        {
            width: parent.width
            text: catalog.i18nc("@title:tab", "Plugins")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
        }
        Rectangle
        {
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
            width: base.width
            text: catalog.i18nc("@title:tab", "Materials")
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
        }
        Rectangle
        {
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
                    id: pluginList
                    model: toolbox.materialsInstalledModel
                    delegate: ToolboxInstalledTile {}
                }
            }
        }
    }
}
