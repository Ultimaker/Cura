// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3
import UM 1.1 as UM

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

Rectangle
{
    id: base
    width: parent.width
    height: childrenRect.height + UM.Theme.getSize("double_margin").height * 8
    color: "transparent"
    Label
    {
        id: heading
        text: "Community Plugins"
        width: parent.width
        height: UM.Theme.getSize("base_unit").width * 4
        verticalAlignment: Text.AlignVCenter
        color: UM.Theme.getColor("text_medium")
        font: UM.Theme.getFont("medium")
    }
    GridLayout
    {
        id: grid
        width: base.width
        anchors
        {
            top: heading.bottom
        }
        columns: 3
        columnSpacing: UM.Theme.getSize("base_unit").width
        rowSpacing: UM.Theme.getSize("base_unit").height

        ToolboxGridTile {}
        ToolboxGridTile {}
        ToolboxGridTile {}
        ToolboxGridTile {}
        ToolboxGridTile {}
        ToolboxGridTile {}
        ToolboxGridTile {}
        ToolboxGridTile {}
    }
}
