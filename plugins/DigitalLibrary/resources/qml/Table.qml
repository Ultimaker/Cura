//Copyright (C) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import Qt.labs.qmlmodels 1.0
import QtQuick 2.15
import QtQuick.Controls 2.15

import UM 1.2 as UM

/*
 * A re-sizeable table of data.
 *
 * This table combines a list of headers with a TableView to show certain roles in a table.
 * The columns of the table can be resized.
 * When the table becomes too big, you can scroll through the table. When a column becomes too small, the contents of
 * the table are elided.
 * The table gets Cura's themeing.
 */
Item
{
    id: tableBase

    required property var columnHeaders //The text to show in the headers of each column.
    property alias model: tableView.model //A TableModel to display in this table. To use a ListModel for the rows, use "rows: listModel.items"
    property int currentRow: -1 //The selected row index.
    property var onDoubleClicked: function(row) {} //Something to execute when double clicked. Accepts one argument: The index of the row that was clicked on.
    property bool allowSelection: true //Whether to allow the user to select items.

    Row
    {
        id: headerBar
        Repeater
        {
            id: headerRepeater
            model: columnHeaders
            Rectangle
            {
                width: Math.max(1, Math.round(tableBase.width / headerRepeater.count))
                height: UM.Theme.getSize("section").height

                color: UM.Theme.getColor("secondary")

                Label
                {
                    id: contentText
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("narrow_margin").width
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("narrow_margin").width

                    text: modelData
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")
                    elide: Text.ElideRight
                }
                Rectangle //Resize handle.
                {
                    anchors
                    {
                        right: parent.right
                        top: parent.top
                        bottom: parent.bottom
                    }
                    width: UM.Theme.getSize("thick_lining").width

                    color: UM.Theme.getColor("thick_lining")

                    MouseArea
                    {
                        anchors.fill: parent

                        cursorShape: Qt.SizeHorCursor
                        drag
                        {
                            target: parent
                            axis: Drag.XAxis
                        }
                        onMouseXChanged:
                        {
                            if(drag.active)
                            {
                                let new_width = parent.parent.width + mouseX;
                                let sum_widths = mouseX;
                                for(let i = 0; i < headerBar.children.length; ++i)
                                {
                                    sum_widths += headerBar.children[i].width;
                                }
                                if(sum_widths > tableBase.width)
                                {
                                    new_width -= sum_widths - tableBase.width; //Limit the total width to not exceed the view.
                                }
                                let width_fraction = new_width / tableBase.width; //Scale with the same fraction along with the total width, if the table is resized.
                                parent.parent.width = Qt.binding(function() { return Math.max(10, Math.round(tableBase.width * width_fraction)) });
                            }
                        }
                    }
                }

                onWidthChanged:
                {
                    tableView.forceLayout(); //Rescale table cells underneath as well.
                }
            }
        }
    }

    TableView
    {
        id: tableView
        anchors
        {
            top: headerBar.bottom
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }

        flickableDirection: Flickable.AutoFlickIfNeeded
        clip: true
        ScrollBar.vertical: ScrollBar
        {
            // Vertical ScrollBar, styled similarly to the scrollBar in the settings panel
            id: verticalScrollBar
            visible: tableView.contentHeight > tableView.height

            background: Rectangle
            {
                implicitWidth: UM.Theme.getSize("scrollbar").width
                radius: Math.round(implicitWidth / 2)
                color: UM.Theme.getColor("scrollbar_background")
            }

            contentItem: Rectangle
            {
                id: scrollViewHandle
                implicitWidth: UM.Theme.getSize("scrollbar").width
                radius: Math.round(implicitWidth / 2)

                color: verticalScrollBar.pressed ? UM.Theme.getColor("scrollbar_handle_down") : verticalScrollBar.hovered ? UM.Theme.getColor("scrollbar_handle_hover") : UM.Theme.getColor("scrollbar_handle")
                Behavior on color { ColorAnimation { duration: 50; } }
            }
        }
        columnWidthProvider: function(column)
        {
            return headerBar.children[column].width; //Cells get the same width as their column header.
        }

        delegate: Rectangle
        {
            implicitHeight: Math.max(1, cellContent.height)

            color: UM.Theme.getColor((tableBase.currentRow == row) ? "primary" : ((row % 2 == 0) ? "main_background" : "viewport_background"))

            Label
            {
                id: cellContent
                width: parent.width

                text: display
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
            }
            TextMetrics
            {
                id: cellTextMetrics
                text: cellContent.text
                font: cellContent.font
                elide: cellContent.elide
                elideWidth: cellContent.width
            }
            UM.TooltipArea
            {
                anchors.fill: parent

                acceptedButtons: Qt.LeftButton
                text: (cellTextMetrics.elidedText == cellContent.text) ? "" : cellContent.text //Show full text in tooltip if it was elided.
                onClicked:
                {
                    if(tableBase.allowSelection)
                    {
                        tableBase.currentRow = row; //Select this row.
                    }
                }
                onDoubleClicked:
                {
                    tableBase.onDoubleClicked(row);
                }
            }
        }

        Connections
        {
            target: model
            function onRowCountChanged()
            {
                tableView.contentY = 0; //When the number of rows is reduced, make sure to scroll back to the start.
            }
        }
    }
}