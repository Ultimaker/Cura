// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Window 2.2

import UM 1.3 as UM
import Cura 1.1 as Cura


Window {
    id: dynamical3DPauseDialog
    minimumWidth: Math.round(UM.Theme.getSize("modal_window_minimum").width/2)
    minimumHeight: Math.round(UM.Theme.getSize("modal_window_minimum").height/2)
    maximumWidth: Math.round(minimumWidth * 1.2)
    maximumHeight: Math.round(minimumHeight * 1.2)
    modality: Qt.ApplicationModal
    width: minimumWidth
    height: minimumHeight
    color: UM.Theme.getColor("main_background")
    title: "Pausas"

    // Globally available.
    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    PausesPage {
        id: pausesPage
    }
}