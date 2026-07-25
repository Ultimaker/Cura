// Copyright (c) 2026 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

// One button in the vertical category TabColumn.  Displays an icon and shows
// the category name as a tooltip on hover.

import QtQuick
import QtQuick.Controls

import UM 1.5 as UM

TabButton
{
    id: tabButton

    property string key: ""
    property var iconSource: ""

    anchors.left: parent ? parent.left : undefined
    width: parent ? parent.width : 0

    background: Rectangle
    {
        id: bgRect
        border.color: UM.Theme.getColor("lining")
        border.width: UM.Theme.getSize("default_lining").height
        color: UM.Theme.getColor(tabButton.checked ? "main_background" : (tabButton.hovered ? "action_button_hovered" : "secondary"))
        visible: tabButton.enabled

        // Overlay that hides the right-hand border of the selected tab so it
        // appears visually connected to the settings panel on the right.
        Rectangle
        {
            id: rightBorderFill
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            // Cover only the right lining strip
            width: bgRect.border.width
            color: bgRect.color
            visible: tabButton.checked
        }

        // Hide the top border of the very first tab (Favorites) when selected,
        // so the column top edge is flush.
        Rectangle
        {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            height: bgRect.border.width
            color: bgRect.color
            visible: tabButton.checked && tabButton.key === "_favorites"
        }
    }

    contentItem: TabContentItem
    {
        iconSource: tabButton.iconSource
    }

    UM.ToolTip
    {
        tooltipText: tabButton.text
        visible: tabButton.hovered
        contentAlignment: UM.Enums.ContentAlignment.AlignLeft
    }
}
