// Copyright (c) 2018 Ultimaker B.V.
import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.1 as UM

ListView
{
    id: backupList
    width: parent.width
    clip: true
    delegate: Item
    {
        width: parent.width
        height: childrenRect.height

        BackupListItem
        {
            id: backupListItem
            width: parent.width
        }

        Divider
        {
            width: parent.width
            anchors.top: backupListItem.bottom
        }
    }
    ScrollBar.vertical: RightSideScrollBar {}
}
