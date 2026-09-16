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
    property int minimumColumnWidth: 50 //The minimum width of a column while resizing.

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
                    anchors.verticalCenter: parent.verticalCenter
                    wrapMode: Text.NoWrap
                    text: modelData
                    font: UM.Theme.getFont("medium_bold")
                    elide: Text.ElideRight
                }

                MouseArea
                {
                    // Resize handle
                    anchors
                    {
                        right: parent.right
                        top: parent.top
                        bottom: parent.bottom
                        rightMargin: -width / 2
                    }
                    width: UM.Theme.getSize("wide_lining").width * 2
                    enabled: index < headerRepeater.count - 1
                    acceptedButtons: Qt.LeftButton
                    cursorShape: enabled ? Qt.SizeHorCursor : Qt.ArrowCursor

                    property var dragLastPos

                    onPressed: function(mouse) { dragLastPos = mapToItem(parent, mouse.x, mouse.y) }

                    onPositionChanged: function(mouse)
                    {
                        let global_pos = mapToItem(parent, mouse.x, mouse.y)
                        let delta = global_pos.x - dragLastPos.x
                        dragLastPos = global_pos

                        let new_widths = []
                        for(let i = 0; i < headerRepeater.count; ++i)
                        {
                            new_widths[i] = headerRepeater.itemAt(i).width;
                        }

                        // Reduce the delta if needed, depending on how much available space we have on the sides
                        if(delta > 0)
                        {
                            let available_extra_width = 0
                            for(let i = index + 1; i < headerRepeater.count; ++i)
                            {
                                available_extra_width += headerRepeater.itemAt(i).width - minimumColumnWidth
                            }

                            delta = Math.min(delta, available_extra_width)
                        }
                        else if(delta < 0)
                        {
                            let available_substracted_width = 0
                            for(let i = index ; i >= 0 ; --i)
                            {
                                available_substracted_width -= headerRepeater.itemAt(i).width - minimumColumnWidth
                            }

                            delta = Math.max(delta, available_substracted_width)
                        }

                        if(delta > 0)
                        {
                            // Enlarge the current element
                            new_widths[index] += delta

                            // Now reduce elements on the right
                            for (let i = index + 1; delta > 0 && i < headerRepeater.count; ++i)
                            {
                                let substract_width = Math.min(delta, headerRepeater.itemAt(i).width - minimumColumnWidth)
                                new_widths[i] -= substract_width
                                delta -= substract_width
                            }
                        }
                        else if(delta < 0)
                        {
                            // Enlarge the element on the right
                            new_widths[index + 1] -= delta

                            // Now reduce elements on the left
                            for (let i = index; delta < 0 && i >= 0; --i)
                            {
                                let substract_width = Math.max(delta, -(headerRepeater.itemAt(i).width - minimumColumnWidth))
                                new_widths[i] += substract_width
                                delta -= substract_width
                            }
                        }

                        // Apply the calculated widths
                        for(let i = 0; i < headerRepeater.count; ++i)
                        {
                            headerRepeater.itemAt(i).width = new_widths[i];
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

    onWidthChanged:
    {
        // Get the previous width but summing the width of actual columns
        let previous_width = 0
        for(let i = 0; i < headerRepeater.count; ++i)
        {
            previous_width += headerRepeater.itemAt(i).width;
        }

        // Now resize the columns while keeping their previous ratios
        for(let i = 0; i < headerRepeater.count; ++i)
        {
            let item = headerRepeater.itemAt(i)
            let item_width_ratio = item.width / previous_width;
            item.width = item_width_ratio * tableBase.width
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