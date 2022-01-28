// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.1 as UM

//
// MenuSeparator with Cura styling.
//
MenuSeparator
{
    padding: 0

    contentItem: Rectangle {
        implicitHeight: UM.Theme.getSize("default_lining").height
        color: UM.Theme.getColor("setting_control_border")
    }
}