// Copyright (c) 2026 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

// Vertical TabBar used as the left-hand category column in the tabbed settings view.

import QtQuick
import QtQuick.Controls

import UM 1.2 as UM

TabBar
{
    id: control

    height: parent ? parent.height : 0
    // Width is set by the parent; expose as a writable property for convenience.

    spacing: -UM.Theme.getSize("default_lining").height

    background: Rectangle
    {
        color: "transparent"
    }

    // Replace the default horizontal contentItem with a vertical ListView.
    contentItem: ListView
    {
        model: control.contentModel
        currentIndex: control.currentIndex

        spacing: control.spacing
        orientation: ListView.Vertical
        boundsBehavior: Flickable.StopAtBounds
        flickableDirection: Flickable.AutoFlickIfNeeded
        snapMode: ListView.SnapToItem
        clip: true

        // Extra bottom padding so the last bookmark tab can scroll fully into view
        footer: Item { height: UM.Theme.getSize("default_margin").height }
    }
}
