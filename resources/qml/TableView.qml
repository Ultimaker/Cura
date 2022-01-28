// Copyright (C) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4 as OldControls // TableView doesn't exist in the QtQuick Controls 2.x in 5.10, so use the old one
import QtQuick.Controls 2.3
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM


OldControls.TableView
{
    itemDelegate: Item
    {
        height: tableCellLabel.implicitHeight

        Label
        {
            id: tableCellLabel
            color: styleData.selected ? UM.Theme.getColor("primary_button_text") : UM.Theme.getColor("text")
            elide: Text.ElideRight
            text: styleData.value
            anchors.fill: parent
            anchors.leftMargin: 10 * screenScaleFactor
            verticalAlignment: Text.AlignVCenter
        }
    }

    rowDelegate: Rectangle
    {
        color: styleData.selected ? UM.Theme.getColor("primary_button") : UM.Theme.getColor("main_background")
        height: UM.Theme.getSize("table_row").height
    }

    // Use the old styling technique since it's the only way to make the scrollbars themed in the TableView
    style: TableViewStyle
    {
        backgroundColor: UM.Theme.getColor("main_background")

        handle: Rectangle
        {
            // Both implicit width and height have to be set, since the handle is used by both the horizontal and the vertical scrollbars
            implicitWidth: UM.Theme.getSize("scrollbar").width
            implicitHeight: UM.Theme.getSize("scrollbar").width
            radius: width / 2
            color: UM.Theme.getColor(styleData.pressed ? "scrollbar_handle_down" : (styleData.hovered ? "scrollbar_handle_hover" : "scrollbar_handle"))
        }

        scrollBarBackground: Rectangle
        {
            // Both implicit width and height have to be set, since the handle is used by both the horizontal and the vertical scrollbars
            implicitWidth: UM.Theme.getSize("scrollbar").width
            implicitHeight: UM.Theme.getSize("scrollbar").width
            color: UM.Theme.getColor("main_background")
        }

        // The little rectangle between the vertical and horizontal scrollbars
        corner: Rectangle
        {
            color: UM.Theme.getColor("main_background")
        }

        // Override the control arrows
        incrementControl: Item { }
        decrementControl: Item { }
    }
}