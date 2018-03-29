// Copyright (c) 2018 Ultimaker B.V.
// PluginBrowser is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2

Rectangle
{
    width: parent.width
    height: 8
    gradient: Gradient
    {
        GradientStop
        {
            position: 0.0
            color: Qt.rgba(0,0,0,0.2)
        }
        GradientStop
        {
            position: 1.0
            color: Qt.rgba(0,0,0,0)
        }
    }
}
