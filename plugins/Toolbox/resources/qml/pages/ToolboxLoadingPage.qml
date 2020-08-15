// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM

Rectangle
{
    id: page
    width: parent.width
    height: parent.height
    color: "transparent"
    Label
    {
        text: catalog.i18nc("@info", "Fetching packages...")
        color: UM.Theme.getColor("text")
        anchors
        {
            centerIn: parent
        }
        renderType: Text.NativeRendering
    }
}
