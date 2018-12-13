// Copyright (c) 2018 Ultimaker B.V.
import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.3 as UM

import "../components"

RowLayout
{
    id: backupListFooter
    width: parent.width
    property bool showInfoButton: false

    ActionButton
    {
        id: infoButton
        text: catalog.i18nc("@button", "Want more?")
        iconSource: "../images/info.svg"
        onClicked: Qt.openUrlExternally("https://goo.gl/forms/QACEP8pP3RV60QYG2")
        visible: backupListFooter.showInfoButton
    }

    ActionButton
    {
        id: createBackupButton
        text: catalog.i18nc("@button", "Backup Now")
        iconSource: "../images/backup.svg"
        enabled: !CuraDrive.isCreatingBackup && !CuraDrive.isRestoringBackup
        onClicked: CuraDrive.createBackup()
        busy: CuraDrive.isCreatingBackup
    }

    ActionCheckBox
    {
        id: autoBackupEnabled
        checked: CuraDrive.autoBackupEnabled
        onClicked: CuraDrive.toggleAutoBackup(autoBackupEnabled.checked)
        label: catalog.i18nc("@checkbox:description", "Automatically create a backup each day that Cura is started.")
    }
}
