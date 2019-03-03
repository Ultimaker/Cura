// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.3
import UM 1.3 as UM
import Cura 1.0 as Cura

Rectangle
{
    id: base

    property var enabled: true

    property var iconSource: null
    color: enabled ? UM.Theme.getColor("monitor_icon_primary") : UM.Theme.getColor("monitor_icon_disabled")
    height: width
    radius: Math.round(0.5 * width)
    width: 24 * screenScaleFactor

    UM.RecolorImage
    {
        id: icon
        anchors
        {
            horizontalCenter: parent.horizontalCenter
            verticalCenter: parent.verticalCenter
        }
        color: UM.Theme.getColor("monitor_icon_accent")
        height: width
        source: iconSource
        width: Math.round(parent.width / 2)
    }

    MouseArea
    {
        id: clickArea
        anchors.fill: parent
        hoverEnabled: base.enabled
        onClicked:
        {
            if (base.enabled)
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
    }
}