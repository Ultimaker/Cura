// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: base
    width: parent.columnSize
    height: childrenRect.height
    Row
    {
        width: parent.width
        height: childrenRect.height
        spacing: Math.floor(UM.Theme.getSize("base_unit").width / 2)
        Rectangle
        {
            id: thumbnail
            width: UM.Theme.getSize("base_unit").width * 6
            height: UM.Theme.getSize("base_unit").height * 6
            color: "white"
            border.width: 1
        }
        Column
        {
            width: UM.Theme.getSize("base_unit").width * 12
            Label
            {
                id: name
                text: "Auto Orientation"
                width: parent.width
                wrapMode: Text.WordWrap
                height: UM.Theme.getSize("base_unit").height * 2
                verticalAlignment: Text.AlignVCenter
                color: UM.Theme.getColor("text")
                font: UM.Theme.getFont("default_bold")
            }
            Label
            {
                id: info
                text: "Automatically orientate your model."
                width: parent.width
                wrapMode: Text.WordWrap
                color: UM.Theme.getColor("text_medium")
                font: UM.Theme.getFont("very_small")
            }
        }
    }
    MouseArea
    {
        anchors.fill: parent
        onClicked: {
            manager.setDetailView("thingy")
        }
    }
}
