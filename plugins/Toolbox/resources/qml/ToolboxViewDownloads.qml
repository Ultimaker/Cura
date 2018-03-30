// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

ScrollView
{
    id: base
    frameVisible: false
    anchors.fill: parent
    style: UM.Theme.styles.scrollview
    Column
    {
        width: base.width
        spacing: UM.Theme.getSize("base_unit").height
        height: childrenRect.height
        anchors
        {
            fill: parent
            topMargin: UM.Theme.getSize("base_unit").height
            bottomMargin: UM.Theme.getSize("base_unit").height
            leftMargin: UM.Theme.getSize("base_unit").width * 2
            rightMargin: UM.Theme.getSize("base_unit").width * 2
        }
        ToolboxShowcase
        {
            id: showcase
        }
        ToolboxGrid
        {
            id: allPlugins
        }
    }
}
