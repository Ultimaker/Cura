// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

ScrollView
{
    frameVisible: false
    width: parent.width
    height: parent.height
    style: UM.Theme.styles.scrollview
    Column
    {
        width: parent.width - 2 * padding
        spacing: UM.Theme.getSize("default_margin").height
        padding: UM.Theme.getSize("wide_margin").height
        height: childrenRect.height + 2 * padding
        ToolboxDownloadsShowcase
        {
            id: showcase
            width: parent.width
        }
        Rectangle
        {
            color: UM.Theme.getColor("lining")
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
        }
        ToolboxDownloadsGrid
        {
            id: allPlugins
            width: parent.width
        }
    }
}
