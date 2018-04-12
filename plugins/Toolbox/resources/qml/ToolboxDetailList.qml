// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Dialogs 1.1
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: base
    ScrollView
    {
        frameVisible: false
        anchors.fill: base
        style: UM.Theme.styles.scrollview
        Column
        {
            anchors
            {
                right: base.right
                topMargin: UM.Theme.getSize("double_margin").height
                bottomMargin: UM.Theme.getSize("double_margin").height
                top: parent.top
            }
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
