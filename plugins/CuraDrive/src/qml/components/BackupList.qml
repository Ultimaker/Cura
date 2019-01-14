// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3

import UM 1.1 as UM

ScrollView
{
    property alias model: backupList.model
    width: parent.width
    clip: true
    ListView
    {
        id: backupList
        width: parent.width
        delegate: Item
        {
            // Add a margin, otherwise the scrollbar is on top of the right most component
            width: parent.width - UM.Theme.getSize("default_margin").width
            height: childrenRect.height

            BackupListItem
            {
                id: backupListItem
                width: parent.width
            }

            Rectangle
            {
                id: divider
                color: UM.Theme.getColor("lining")
                height: UM.Theme.getSize("default_lining").height
            }
        }
    }
}
