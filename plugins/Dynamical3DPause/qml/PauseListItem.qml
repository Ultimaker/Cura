// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Item {
    id: pauseListItem
    width: parent.width
    height:  dataRow.height

    // Backup details toggle animation.
    Behavior on height
    {
        PropertyAnimation
        {
            duration: 70
        }
    }

    RowLayout {
        id: dataRow
        spacing: UM.Theme.getSize("wide_margin").width
        width: parent.width
        height: 50 * screenScaleFactor



        Label{
            text: modelData
            color: UM.Theme.getColor("text")
            elide: Text.ElideRight
            Layout.minimumWidth: 100 * screenScaleFactor
            Layout.maximumWidth: 500 * screenScaleFactor
            Layout.fillWidth: true
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
        }

        UM.SimpleButton{
            width: UM.Theme.getSize("message_close").width
            height: UM.Theme.getSize("message_close").height
            color: UM.Theme.getColor("small_button_text")
            hoverColor: UM.Theme.getColor("small_button_text_hover")
            iconSource: UM.Theme.getIcon("cross1")
            onClicked: confirmDeleteDialog.visible = true
        }
    }

    // BackupListItemDetails
    // {
    //     id: backupDetails
    //     backupDetailsData: modelData
    //     width: parent.width
    //     visible: parent.showDetails
    //     anchors.top: dataRow.bottom
    // }

    MessageDialog {
        id: confirmDeleteDialog
        title: catalog.i18nc("@dialog:title", "Eliminar punto de pausa")
        text: catalog.i18nc("@dialog:info", "¿Estás seguro de eliminar la pausa?")
        standardButtons: StandardButton.Yes | StandardButton.No
        onYes: Dynamical3DPause.removePoint(modelData)
    }

    

    
}
