// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.0 as Cura

import "../components"

RowLayout
{
    id: backupListFooter
    width: parent.width
    property bool showInfoButton: false

    Cura.PrimaryButton
    {
        id: infoButton
        text: catalog.i18nc("@button", "Want more?")
        iconSource: UM.Theme.getIcon("info")
        onClicked: Qt.openUrlExternally("https://goo.gl/forms/QACEP8pP3RV60QYG2")
        visible: backupListFooter.showInfoButton
    }

    Cura.PrimaryButton
    {
        id: createBackupButton
        text: catalog.i18nc("@button", "Backup Now")
        iconSource: UM.Theme.getIcon("plus")
        enabled: !CuraDrive.isCreatingBackup && !CuraDrive.isRestoringBackup
        onClicked: CuraDrive.createBackup()
        busy: CuraDrive.isCreatingBackup
    }

    Cura.CheckBoxWithTooltip
    {
        id: autoBackupEnabled
        checked: CuraDrive.autoBackupEnabled
        onClicked: CuraDrive.toggleAutoBackup(autoBackupEnabled.checked)
        text: catalog.i18nc("@checkbox:description", "Auto Backup")
        tooltip: catalog.i18nc("@checkbox:description", "Automatically create a backup each day that Cura is started.")
    }
}
