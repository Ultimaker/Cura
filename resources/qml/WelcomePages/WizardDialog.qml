// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Window 2.2

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This is a dialog for showing a set of processes that's defined in a WelcomePagesModel or some other Qt ListModel with
// a compatible interface.
//
Window
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    id: dialog

    flags: Qt.Dialog
    modality: Qt.ApplicationModal

    minimumWidth: 580 * screenScaleFactor
    minimumHeight: 600 * screenScaleFactor
    maximumWidth: minimumWidth
    maximumHeight: minimumHeight

    color: UM.Theme.getColor("main_background")

    property var model: null  // Needs to be set by whoever is using this dialog.
    property alias progressBarVisible: wizardPanel.progressBarVisible
    property alias hasCancelButton: cancelButton.visible

    onVisibilityChanged:
    {
        if (visible)
        {
            model.resetState()
        }
    }

    WizardPanel
    {
        id: wizardPanel
        anchors.fill: parent
        model: dialog.model
    }

    // Close this dialog when there's no more page to show
    Connections
    {
        target: model
        onAllFinished: dialog.hide()
    }

    Cura.SecondaryButton
    {
        id: cancelButton

        text: catalog.i18nc("@button", "Cancel")

        visible: false

        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: UM.Theme.getSize("default_margin").width
        anchors.leftMargin: UM.Theme.getSize("wide_margin").width

        enabled: true
        onClicked: dialog.visible = false
    }
}
