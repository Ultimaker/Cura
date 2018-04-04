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
    width: UM.Theme.getSize("toolbox_thumbnail_large").width
    height: UM.Theme.getSize("toolbox_thumbnail_large").width
    Rectangle
    {
        color: "white"
        width: UM.Theme.getSize("base_unit").width * 8
        height: UM.Theme.getSize("base_unit").width * 8
        border.width: 1
        anchors
        {
            top: parent.top
            horizontalCenter: parent.horizontalCenter
        }
    }
    Label
    {
        text: "Solidworks Integration"
        anchors
        {
            bottom: parent.bottom
            horizontalCenter: parent.horizontalCenter
        }
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignHCenter
        height: UM.Theme.getSize("base_unit").width * 4
        width: parent.width
        color: UM.Theme.getColor("text")
        font: UM.Theme.getFont("medium_bold")
    }
}
