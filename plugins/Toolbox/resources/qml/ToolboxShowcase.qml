// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

Rectangle
{
    id: base
    width: parent.width
    height: childrenRect.height
    color: "transparent"
    Label
    {
        id: heading
        text: "Top Downloads"
        width: parent.width
        height: UM.Theme.getSize("base_unit").width * 4
        verticalAlignment: Text.AlignVCenter
        color: UM.Theme.getColor("text_medium")
        font: UM.Theme.getFont("medium")
    }
    Row
    {
        height: childrenRect.height
        width: childrenRect.width
        spacing: UM.Theme.getSize("base_unit").width * 2
        anchors
        {
            horizontalCenter: parent.horizontalCenter
            top: heading.bottom    
        }

        ToolboxShowcaseTile {}
        ToolboxShowcaseTile {}
        ToolboxShowcaseTile {}
    }
    Rectangle
    {
        color: UM.Theme.getColor("text_medium")
        width: parent.width
        height: UM.Theme.getSize("base_unit").height / 6
        anchors
        {
            bottom: parent.bottom
        }
    }
}
