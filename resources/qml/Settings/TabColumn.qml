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
        // Right-edge lining that visually connects the column to the settings panel.
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: UM.Theme.getSize("default_lining").width
        color: UM.Theme.getColor("lining")
        visible: parent.enabled
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
    }
}
