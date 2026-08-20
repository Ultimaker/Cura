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
        color: UM.Theme.getColor(tabButton.checked ? "main_background" : (tabButton.hovered ? "action_button_hovered" : "secondary"))
        visible: tabButton.enabled
        border.color: UM.Theme.getColor("border_main")
        border.width: UM.Theme.getSize("default_lining").width

        // Cover the right border with the tab's own background color.
        Rectangle
        {
            anchors
            {
                top:          parent.top
                topMargin:    parent.border.width
                right:        parent.right
                bottom:       parent.bottom
                bottomMargin: parent.border.width
            }
            width: parent.border.width
            color: parent.color
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
