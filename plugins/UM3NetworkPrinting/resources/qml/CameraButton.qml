// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 2.4
import QtQuick.Controls.Styles 1.3
import UM 1.3 as UM
import Cura 1.0 as Cura

Button
{
    property var iconSource: null
    width: UM.Theme.getSize("button").width * 0.75 //Matching the size of the content of tool buttons.
    height: UM.Theme.getSize("button").height * 0.75

    hoverEnabled: true

    background: Rectangle
    {
        anchors.fill: parent
        radius: 0.5 * width
        color: parent.enabled ? (parent.hovered ? UM.Theme.getColor("monitor_secondary_button_hover") : "transparent") : UM.Theme.getColor("monitor_icon_disabled")
    }

    UM.RecolorImage
    {
        id: icon
        anchors
        {
            horizontalCenter: parent.horizontalCenter
            verticalCenter: parent.verticalCenter
        }
        color: enabled ? UM.Theme.getColor("primary") : UM.Theme.getColor("main_background")
        height: width
        source: iconSource
        width: Math.round(parent.width / 2)
    }

    onClicked:
    {
        if (OutputDevice.activeCameraUrl != "")
        {
            OutputDevice.setActiveCameraUrl("")
        }
        else
        {
            OutputDevice.setActiveCameraUrl(modelData.cameraUrl)
        }
    }
}
