// Copyright (c) 2018 Ultimaker B.V.
import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.1

import UM 1.1 as UM

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
        spacing: UM.Theme.getSize("default_margin").width * 2
        width: parent.width
        height: 50 * screenScaleFactor

        ActionButton
        {
            color: "transparent"
            hoverColor: "transparent"
            textColor: UM.Theme.getColor("text")
            textHoverColor: UM.Theme.getColor("primary")
            iconSource: "../images/info.svg"
            onClicked: backupListItem.showDetails = !backupListItem.showDetails
        }

        Label
        {
            text: new Date(model["generated_time"]).toLocaleString(UM.Preferences.getValue("general/language"))
            color: UM.Theme.getColor("text")
            elide: Text.ElideRight
            Layout.minimumWidth: 100 * screenScaleFactor
            Layout.maximumWidth: 500 * screenScaleFactor
            Layout.fillWidth: true
            renderType: Text.NativeRendering
        }

        Label
        {
            text: model["data"]["description"]
            color: UM.Theme.getColor("text")
            elide: Text.ElideRight
            Layout.minimumWidth: 100 * screenScaleFactor
            Layout.maximumWidth: 500 * screenScaleFactor
            Layout.fillWidth: true
            renderType: Text.NativeRendering
        }

        ActionButton
        {
            text: catalog.i18nc("@button", "Restore")
            color: "transparent"
            hoverColor: "transparent"
            textColor: UM.Theme.getColor("text")
            textHoverColor: UM.Theme.getColor("text_link")
            enabled: !CuraDrive.isCreatingBackup && !CuraDrive.isRestoringBackup
            onClicked: confirmRestoreDialog.visible = true
        }

        ActionButton
        {
            color: "transparent"
            hoverColor: "transparent"
            textColor: UM.Theme.getColor("setting_validation_error")
            textHoverColor: UM.Theme.getColor("setting_validation_error")
            iconSource: "../images/delete.svg"
            onClicked: confirmDeleteDialog.visible = true
        }
    }

    BackupListItemDetails
    {
        id: backupDetails
        backupDetailsData: model
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
        onYes: CuraDrive.deleteBackup(model["backup_id"])
    }

    MessageDialog
    {
        id: confirmRestoreDialog
        title: catalog.i18nc("@dialog:title", "Restore Backup")
        text: catalog.i18nc("@dialog:info", "You will need to restart Cura before your backup is restored. Do you want to close Cura now?")
        standardButtons: StandardButton.Yes | StandardButton.No
        onYes: CuraDrive.restoreBackup(model["backup_id"])
    }
}
