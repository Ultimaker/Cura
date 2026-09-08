// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Window 2.2

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This is an Item that tries to mimic a dialog for showing the welcome process.
//
Item
{
    property alias model: wizardPanel.model
    property alias progressBarVisible: wizardPanel.progressBarVisible

    id: base

    anchors.fill: parent
    z: 100

    MouseArea
    {
        // Prevent all mouse events from passing through.
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.AllButtons
    }

    Rectangle
    {
        color: UM.Theme.getColor("window_disabled_background")
        opacity: 0.7
        anchors.fill: parent
    }

    WizardPanel
    {
        id: wizardPanel
        UM.I18nCatalog { id: catalog; name: "cura" }

        anchors.centerIn: parent

        width: UM.Theme.getSize("welcome_wizard_window").width
        height: UM.Theme.getSize("welcome_wizard_window").height
    }

    // Close this dialog when there's no more page to show
    Connections
    {
        target: model
        function onAllFinished() { base.destroy() }
    }
}
