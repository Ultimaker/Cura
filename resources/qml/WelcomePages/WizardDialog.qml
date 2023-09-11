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

    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    maximumWidth: minimumWidth
    maximumHeight: minimumHeight

    color: UM.Theme.getColor("main_background")

    property var model: null  // Needs to be set by whoever is using this dialog.
    property alias progressBarVisible: wizardPanel.progressBarVisible

    WizardPanel
    {
        id: wizardPanel
        anchors.fill: parent
        model: dialog.model
        visible: dialog.visible
    }

    // Close this dialog when there's no more page to show
    Connections
    {
        target: model
        function onAllFinished() { dialog.hide() }
    }
}
