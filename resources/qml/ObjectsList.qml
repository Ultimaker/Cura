// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

import UM 1.3 as UM
import Cura 1.0 as Cura

import "Menus"

Rectangle
{
    id: base;

    color: UM.Theme.getColor("tool_panel_background")

    width: UM.Theme.getSize("objects_menu_size").width
    height: UM.Theme.getSize("objects_menu_size").height

    Button
    {
        id: openFileButton;
        text: catalog.i18nc("@action:button","Open File");
        iconSource: UM.Theme.getIcon("load")
        style: UM.Theme.styles.tool_button
        tooltip: '';
        anchors
        {
            top: parent.top;
            topMargin: UM.Theme.getSize("default_margin").height;
            left: parent.left;
            leftMargin: UM.Theme.getSize("default_margin").height;
        }
        action: Cura.Actions.open;
    }

    ListModel
    {
        id: objectsListModel;

        ListElement {
            name: "Apple"
            cost: 2.45
        }
        ListElement {
            name: "Orange"
            cost: 3.25
        }
        ListElement {
            name: "Banana"
            cost: 1.95
        }
    }

    Component {
        id: objectDelegate
        Rectangle {
            height: 30

            Text {
                text: name
                color: red
            }
            //Text { text: '$' + cost }
        }
    }

    ListView
    {
        model: objectsListModel;
        anchors
        {
            top: openFileButton.bottom;
            topMargin: UM.Theme.getSize("default_margin").height;
            left: parent.left;
            leftMargin: UM.Theme.getSize("default_margin").height;
        }
        width: parent.width - 2 * UM.Theme.getSize("default_margin").height
        height: 100

        delegate: objectDelegate
    }

}
