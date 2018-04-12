// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

Rectangle
{
    id: base
    width: parent.width
    height: parent.height
    color: "transparent"
    Label
    {
        text: "Fetching packages..."
        anchors
        {
            centerIn: parent
        }
    }
}
