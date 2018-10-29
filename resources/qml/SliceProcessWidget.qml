// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.1 as UM
import Cura 1.0 as Cura

Column
{
    id: widget

    spacing: UM.Theme.getSize("default_margin").height

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    property real progress: UM.Backend.progress
    property int backendState: UM.Backend.state

    Rectangle
    {
        id: progressBar
        width: parent.width
        height: UM.Theme.getSize("progressbar").height
        visible: widget.backendState == 2
        radius: UM.Theme.getSize("progressbar_radius").width
        color: UM.Theme.getColor("progressbar_background")

        Rectangle
        {
            width: Math.max(parent.width * base.progress)
            height: parent.height
            radius: UM.Theme.getSize("progressbar_radius").width
            color: UM.Theme.getColor("progressbar_control")
        }
    }

    Cura.ActionButton
    {
        id: prepareButton
        width: UM.Theme.getSize("action_panel_button").width
        height: UM.Theme.getSize("action_panel_button").height
        text: widget.backendState == 1 ? catalog.i18nc("@button", "Prepare") : catalog.i18nc("@button", "Cancel")
        onClicked:
        {
            if ([1, 5].indexOf(widget.backendState) != -1)
            {
                CuraApplication.backend.forceSlice()
            }
            else
            {
                CuraApplication.backend.stopSlicing()
            }
        }
    }
}
