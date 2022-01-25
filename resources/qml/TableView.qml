//Copyright (C) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import Qt.labs.qmlmodels 1.0
import QtQuick 2.15
import QtQuick.Controls 2.15

import UM 1.5 as UM

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
                width: Math.round(tableBase.width / headerRepeater.count)
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
                Rectangle
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
                                parent.parent.width = Math.max(10, parent.parent.width + mouseX); //Don't go smaller than 10 pixels, to make sure you can still scale it back.
                                let sum_widths = 0;
                                for(let i = 0; i < headerBar.children.length; ++i)
                                {
                                    sum_widths += headerBar.children[i].width;
                                }
                                if(sum_widths > tableBase.width)
                                {
                                    parent.parent.width -= sum_widths - tableBase.width; //Limit the total width to not exceed the view.
                                }
                            }
                            tableView.forceLayout();
                        }
                    }
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

        clip: true
        ScrollBar.vertical: UM.ScrollBar {}
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
            MouseArea
            {
                anchors.fill: parent

                enabled: tableBase.allowSelection
                onClicked:
                {
                    tableBase.currentRow = row; //Select this row.
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