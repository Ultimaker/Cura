// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Item
{
    id: backupListItem
    width: parent.width
    height: showDetails ? dataRow.height + backupDetails.height : dataRow.height
    property bool showDetails: false

    // Backup details toggle animation.
    Behavior on height
    {
        PropertyAnimation
        {
            duration: 70
        }
    }

    RowLayout
    {
        id: dataRow
        spacing: UM.Theme.getSize("wide_margin").width
        width: parent.width
        height: 50 * screenScaleFactor

        UM.SimpleButton
        {
            width: UM.Theme.getSize("section_icon").width
            height: UM.Theme.getSize("section_icon").height
            color: UM.Theme.getColor("small_button_text")
            hoverColor: UM.Theme.getColor("small_button_text_hover")
            iconSource: UM.Theme.getIcon("Information")
            onClicked: backupListItem.showDetails = !backupListItem.showDetails
        }

        Label
        {
            text: new Date(modelData.generated_time).toLocaleString(UM.Preferences.getValue("general/language"))
            color: UM.Theme.getColor("text")
            elide: Text.ElideRight
            Layout.minimumWidth: 100 * screenScaleFactor
            Layout.maximumWidth: 500 * screenScaleFactor
            Layout.fillWidth: true
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
        }

        Label
        {
            text: modelData.metadata.description
            color: UM.Theme.getColor("text")
            elide: Text.ElideRight
            Layout.minimumWidth: 100 * screenScaleFactor
            Layout.maximumWidth: 500 * screenScaleFactor
            Layout.fillWidth: true
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
        }

        Cura.SecondaryButton
        {
            text: catalog.i18nc("@button", "Restore")
            enabled: !CuraDrive.isCreatingBackup && !CuraDrive.isRestoringBackup
            onClicked: confirmRestoreDialog.visible = true
            busy: CuraDrive.backupIdBeingRestored == modelData.backup_id && CuraDrive.isRestoringBackup
        }

        UM.SimpleButton
        {
            width: UM.Theme.getSize("message_close").width
            height: UM.Theme.getSize("message_close").height
            color: UM.Theme.getColor("small_button_text")
            hoverColor: UM.Theme.getColor("small_button_text_hover")
            iconSource: UM.Theme.getIcon("Cancel")
            onClicked: confirmDeleteDialog.visible = true
        }
    }

    BackupListItemDetails
    {
        id: backupDetails
        backupDetailsData: modelData
        width: parent.width
        visible: parent.showDetails
        anchors.top: dataRow.bottom
    }

    MessageDialog
    {
        id: confirmDeleteDialog
        title: catalog.i18nc("@dialog:title", "Delete Backup")
        text: catalog.i18nc("@dialog:info", "Are you sure you want to delete this backup? This cannot be undone.")
        standardButtons: StandardButton.Yes | StandardButton.No
        onYes: CuraDrive.deleteBackup(modelData.backup_id)
    }

    MessageDialog
    {
        id: confirmRestoreDialog
        title: catalog.i18nc("@dialog:title", "Restore Backup")
        text: catalog.i18nc("@dialog:info", "You will need to restart Cura before your backup is restored. Do you want to close Cura now?")
        standardButtons: StandardButton.Yes | StandardButton.No
        onYes: CuraDrive.restoreBackup(modelData.backup_id)
    }
}
