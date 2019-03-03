// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: objectSelector
    width: UM.Theme.getSize("objects_menu_size").width
    property bool opened: UM.Preferences.getValue("cura/show_list_of_files")

    Button
    {
        id: openCloseButton
        width: UM.Theme.getSize("standard_arrow").width
        height: UM.Theme.getSize("standard_arrow").height
        hoverEnabled: true

        anchors
        {
            bottom: contents.top
            horizontalCenter: parent.horizontalCenter
        }

        contentItem: UM.RecolorImage
        {
            anchors.fill: parent
            sourceSize.width: width
            color: openCloseButton.hovered ? UM.Theme.getColor("small_button_text_hover") : UM.Theme.getColor("small_button_text")
            source: objectSelector.opened ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_top")
        }

        background: Item {}

        onClicked:
        {
            UM.Preferences.setValue("cura/show_list_of_files", !objectSelector.opened)
            objectSelector.opened = UM.Preferences.getValue("cura/show_list_of_files")
        }
    }

    Item
    {
        id: contents
        width: parent.width
        visible: objectSelector.opened
        height: visible ? scroll.height : 0

        Behavior on height { NumberAnimation { duration: 100 } }

        anchors.bottom: parent.bottom

        ScrollView
        {
            id: scroll
            width: parent.width
            clip: true
            leftPadding: UM.Theme.getSize("default_lining").width
            rightPadding: UM.Theme.getSize("default_lining").width

            contentItem: ListView
            {
                id: listView

                // Can't use parent.width since the parent is the flickable component and not the ScrollView
                width: scroll.width - scroll.leftPadding - scroll.rightPadding
                property real maximumHeight: UM.Theme.getSize("objects_menu_size").height

                // We use an extra property here, since we only want to to be informed about the content size changes.
                onContentHeightChanged:
                {
                    scroll.height = Math.min(contentHeight, maximumHeight)
                }

                Component.onCompleted:
                {
                    scroll.height = Math.min(contentHeight, maximumHeight)
                }
                model: Cura.ObjectsModel {}

                delegate: ObjectItemButton
                {
                    text: model.name
                    width: listView.width

                    checked: model.selected
                }
            }
        }
    }
}
