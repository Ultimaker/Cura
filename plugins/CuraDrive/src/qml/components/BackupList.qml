// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.2
import QtQuick.Layouts 1.3

import UM 1.5 as UM

ListView
{
    clip: true
    ScrollBar.vertical: UM.ScrollBar {}

    delegate: Item
    {
        // Add a margin, otherwise the scrollbar is on top of the right most component
        width: parent.width - UM.Theme.getSize("scrollbar").width
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
