// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1

import UM 1.2 as UM

SettingItem
{
    contents: Label
    {
        anchors.fill: parent
        text: value + " " + unit;
        color: UM.Theme.getColor("setting_control_text")

        verticalAlignment: Qt.AlignVCenter
    }
}
