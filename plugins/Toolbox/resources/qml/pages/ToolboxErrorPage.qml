// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.2
import QtQuick.Controls.Styles 2.2

Rectangle
{
    id: page
    width: parent.width
    height: parent.height
    color: "transparent"
    Label
    {
        text: catalog.i18nc("@info", "Could not connect to the Cura Package database. Please check your connection.")
        anchors
        {
            centerIn: parent
        }
        renderType: Text.NativeRendering
    }
}
