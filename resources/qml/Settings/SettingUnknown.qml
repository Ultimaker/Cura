// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.5 as UM

SettingItem
{
    contents: UM.Label
    {
        anchors.fill: parent
        text: propertyProvider.properties.value + " " + unit
    }
}
