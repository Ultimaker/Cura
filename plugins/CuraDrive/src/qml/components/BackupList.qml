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
    ListView
    {
        id: backupList
        width: parent.width
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
    }
}
