// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import UM 1.4 as UM

Rectangle
{
    property var packageData

    width: parent.width
    height: UM.Theme.getSize("card").height

    color: UM.Theme.getColor("main_background")
    radius: UM.Theme.getSize("default_radius").width

    Label
    {
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: Math.round((parent.height - height) / 2)

        text: packageData.displayName
        font: UM.Theme.getFont("medium_bold")
        color: UM.Theme.getColor("text")
    }
}
