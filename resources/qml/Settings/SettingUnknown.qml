// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15

import UM 1.2 as UM

SettingItem
{
    contents: Label
    {
        anchors.fill: parent
        text: propertyProvider.properties.value + " " + unit
        renderType: Text.NativeRendering
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        verticalAlignment: Text.AlignVCenter
    }
}
