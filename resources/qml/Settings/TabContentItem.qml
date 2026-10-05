// Copyright (c) 2026 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

// Icon-only content item for a TabColumnButton.

import QtQuick
import QtQuick.Controls

import UM 1.5 as UM

Item
{
    property alias iconSource: icon.source

    implicitHeight: icon.height + UM.Theme.getSize("default_margin").height

    UM.ColorImage
    {
        id: icon
        anchors.centerIn: parent
        color: UM.Theme.getColor("setting_category_text")
        width: visible ? UM.Theme.getSize("section_icon").width : 0
        height: UM.Theme.getSize("section_icon").height
    }
}
