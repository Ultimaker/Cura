// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Cura.ExpandableComponent
{
    id: base

    headerCornerSide: Cura.RoundedRectangle.Direction.All
    contentAlignment: Cura.ExpandablePopup.ContentAlignment.AlignLeft
    contentHeaderTitle: catalog.i18nc("@label", "Object list")

    headerItem: Item
    {
        anchors.fill: parent
        UM.RecolorImage
        {
            id: buttonIcon
            anchors.centerIn: parent
            source: UM.Theme.getIcon("load")
            width: UM.Theme.getSize("button_icon").width
            height: UM.Theme.getSize("button_icon").height
            color: UM.Theme.getColor("icon")

            sourceSize.height: height
        }
    }

    contentItem: Item
    {
        id: popup
        width: UM.Theme.getSize("machine_selector_widget_content").width

        ScrollView
        {
            id: scroll
            width: parent.width
            clip: true
            leftPadding: UM.Theme.getSize("default_lining").width
            rightPadding: UM.Theme.getSize("default_lining").width

            ListView
            {
                id: listView

                // Can't use parent.width since the parent is the flickable component and not the ScrollView
                width: scroll.width - scroll.leftPadding - scroll.rightPadding
                property real maximumHeight: UM.Theme.getSize("machine_selector_widget_content").height - buttonRow.height

                // We use an extra property here, since we only want to to be informed about the content size changes.
                onContentHeightChanged:
                {
                    scroll.height = Math.min(contentHeight, maximumHeight)
                    popup.height = scroll.height + buttonRow.height
                }

                Component.onCompleted:
                {
                    scroll.height = Math.min(contentHeight, maximumHeight)
                    popup.height = scroll.height + buttonRow.height
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

        Rectangle
        {
            id: separator

            anchors.top: scroll.bottom
            width: parent.width
            height: UM.Theme.getSize("default_lining").height
            color: UM.Theme.getColor("lining")
        }

        Row
        {
            id: buttonRow

            // The separator is inside the buttonRow. This is to avoid some weird behaviours with the scroll bar.
            anchors.top: separator.top
            anchors.horizontalCenter: parent.horizontalCenter
            padding: UM.Theme.getSize("default_margin").width
            spacing: UM.Theme.getSize("default_margin").width

            Cura.SecondaryButton
            {
                leftPadding: UM.Theme.getSize("default_margin").width
                rightPadding: UM.Theme.getSize("default_margin").width
                text: catalog.i18nc("@button", "Add file")
                onClicked: Cura.Actions.open.trigger()
            }
        }
    }
}
