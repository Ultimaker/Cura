//Copyright (C) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

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
    property string sectionRole: ""

    property alias flickableDirection: tableView.flickableDirection
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

                color: UM.Theme.getColor("main_background")
                border.width: UM.Theme.getSize("default_lining").width
                border.color: UM.Theme.getColor("thick_lining")

                UM.Label
                {
                    id: contentText
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("narrow_margin").width
                    wrapMode: Text.NoWrap
                    text: modelData
                    font: UM.Theme.getFont("medium_bold")
                    elide: Text.ElideRight
                }
                Item
                {
                    //Resize handle.
                    anchors
                    {
                        right: parent.right
                        top: parent.top
                        bottom: parent.bottom
                    }
                    width: UM.Theme.getSize("default_lining").width

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

                onWidthChanged: tableView.forceLayout(); //Rescale table cells underneath as well.
            }
        }
    }
    Rectangle
    {
        color: UM.Theme.getColor("main_background")
        anchors
        {
            top: headerBar.bottom
            topMargin: -UM.Theme.getSize("default_lining").width
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("thick_lining")
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
            margins: UM.Theme.getSize("default_lining").width
        }

        flickableDirection: Flickable.AutoFlickIfNeeded
        contentWidth: -1 // AUto calculate the contendWidth
        clip: true
        ScrollBar.vertical: UM.ScrollBar {}
        columnWidthProvider: function(column)
        {
            return headerBar.children[column].width; //Cells get the same width as their column header.
        }

        delegate: Rectangle
        {
            implicitHeight: Math.max(1, cellContent.height)

            color: UM.Theme.getColor((tableBase.currentRow == row) ? "text_selection" : "main_background")

            UM.Label
            {
                id: cellContent
                anchors
                {
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                    right: parent.right
                }
                wrapMode: Text.NoWrap
                text: display
                verticalAlignment: Text.AlignVCenter
                elide: Text.ElideRight
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
            }

            MouseArea
            {
                anchors.fill: parent
                propagateComposedEvents: true
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

    Connections
    {
        target: model
        function onRowsChanged()
        {
            let first_column = model.columns[0].display;
            if(model.rows.length > 0 && model.rows[0][first_column].startsWith("<b>")) //First item is already a section header.
            {
                return; //Assume we already added section headers. Prevent infinite recursion.
            }
            if(sectionRole === "" || model.rows.length == 0) //No section headers, or no items at all.
            {
                tableView.model.rows = model.rows;
                return;
            }

            //Insert section headers in the rows.
            let last_section = "";
            let new_rows = [];
            for(let i = 0; i < model.rows.length; ++i)
            {
                let item_section = model.rows[i][sectionRole];
                if(item_section !== last_section) //Starting a new section.
                {
                    let section_header = {};
                    for(let key in model.rows[i])
                    {
                        section_header[key] = (key === first_column) ? "<b>" + item_section + "</b>" : ""; //Put the section header in the first column.
                    }
                    new_rows.push(section_header); //Add a row representing a section header.
                    last_section = item_section;
                }
                new_rows.push(model.rows[i]);
            }
            tableView.model.rows = new_rows;
        }
    }
}