// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Window 2.2
import QtGraphicalEffects 1.0  // For the DropShadow

import UM 1.3 as UM
import Cura 1.1 as Cura


Window
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    title: catalog.i18nc("@title", "Welcome to Ultimaker Cura")
    modality: Qt.ApplicationModal
    flags: Qt.Window | Qt.FramelessWindowHint

    width: 580  // TODO
    height: 600  // TODO
    color: "transparent"

    property int shadowOffset: 1 * screenScaleFactor

    property alias currentStep: stepPanel.currentStep

    StepPanel
    {
        id: stepPanel
        anchors.fill: parent
        currentStep: 0
        model: CuraApplication.getWelcomePagesModel()
    }

    // Drop shadow around the panel
    DropShadow
    {
        id: shadow
        radius: UM.Theme.getSize("monitor_shadow_radius").width
        anchors.fill: stepPanel
        source: stepPanel
        horizontalOffset: shadowOffset
        verticalOffset: shadowOffset
        color: UM.Theme.getColor("monitor_shadow")
        transparentBorder: true
    }

    // Close this dialog when there's no more page to show
    Connections
    {
        target: stepPanel
        onPassLastPage: close()
    }
}
