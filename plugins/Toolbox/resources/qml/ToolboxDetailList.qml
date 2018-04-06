// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: base
    anchors
    {
        topMargin: UM.Theme.getSize("default_margin").height
        bottomMargin: UM.Theme.getSize("default_margin").height
        leftMargin: UM.Theme.getSize("double_margin").width
        rightMargin: UM.Theme.getSize("double_margin").width
    }
    ScrollView
    {
        frameVisible: false
        anchors.fill: base
        style: UM.Theme.styles.scrollview
        Column
        {
            height: childrenRect.height
            spacing: UM.Theme.getSize("default_margin").height
            Repeater
            {
                model: manager.packagesModel
                delegate: ToolboxDetailTile {}
            }
        }
    }
}
