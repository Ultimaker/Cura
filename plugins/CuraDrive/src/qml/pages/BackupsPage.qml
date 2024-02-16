// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.1 as Cura

import "../components"

Item
{
    id: backupsPage
    anchors.fill: parent
    anchors.margins: UM.Theme.getSize("wide_margin").width

    ColumnLayout
    {
        spacing: UM.Theme.getSize("wide_margin").height
        width: parent.width
        anchors.fill: parent

        UM.Label
        {
            id: backupTitle
            text: catalog.i18nc("@title", "My Backups")
            font: UM.Theme.getFont("large")
            Layout.fillWidth: true
        }

        UM.Label
        {
            text: catalog.i18nc("@empty_state",
                "You don't have any backups currently. Use the 'Backup Now' button to create one.")
            width: parent.width
            wrapMode: Label.WordWrap
            visible: backupList.model.length == 0
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        BackupList
        {
            id: backupList
            model: CuraDrive.backups
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        UM.Label
        {
            text: catalog.i18nc("@backup_limit_info",
                "During the preview phase, you'll be limited to 5 visible backups. Remove a backup to see older ones.")
            width: parent.width
            wrapMode: Label.WordWrap
            visible: backupList.model.length > 4
        }

        BackupListFooter
        {
            id: backupListFooter
            
        }
    }
}
