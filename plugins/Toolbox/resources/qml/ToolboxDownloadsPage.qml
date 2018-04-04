// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

// TODO: Switch to QtQuick.Controls 2.x and remove QtQuick.Controls.Styles

ScrollView
{
    id: base
    frameVisible: false
    width: parent.width
    height: parent.height
    style: UM.Theme.styles.scrollview
    Column
    {
        width: base.width
        spacing: UM.Theme.getSize("base_unit").height
        padding: UM.Theme.getSize("base_unit").height * 2
        height: childrenRect.height + 2 * padding
        ToolboxDownloadsShowcase
        {
            id: showcase
            width: parent.width - 2 * parent.padding
        }
        Rectangle
        {
            color: UM.Theme.getColor("text_medium")
            width: parent.width - 2 * parent.padding
            height: UM.Theme.getSize("base_unit").height / 6
        }
        ToolboxDownloadsGrid
        {
            id: allPlugins
            width: parent.width - 2 * parent.padding
        }
    }
}
