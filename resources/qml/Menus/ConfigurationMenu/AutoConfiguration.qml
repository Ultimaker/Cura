// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.3 as UM

Item
{
    Label
    {
        id: header
        text: catalog.i18nc("@header", "Configurations")
        font: UM.Theme.getFont("large")
        color: UM.Theme.getColor("text")

        anchors
        {
            top: parent.top
            left: parent.left
            right: parent.right
        }
    }
}