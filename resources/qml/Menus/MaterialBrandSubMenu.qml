// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4
import QtQuick.Layouts 2.7

import UM 1.5 as UM
import Cura 1.7 as Cura

Popup
{
    id: materialBrandSubMenu

    // There is a bug where hovering the bottom half of the last element causes the popup to close.
    // Undo this commit if you find a fix.
    bottomPadding: -UM.Theme.getSize("thin_margin").height
    topPadding: UM.Theme.getSize("thin_margin").height

    implicitWidth: scrollViewContent.width + scrollbar.width + leftPadding + rightPadding
    implicitHeight: scrollViewContent.height + bottomPadding + topPadding + (2 * UM.Theme.getSize("thin_margin").height)

    // offset position relative to the parent
    property int implicitX: parent.width - UM.Theme.getSize("default_lining").width
    property int implicitY: -UM.Theme.getSize("thin_margin").height

    default property alias contents: scrollViewContent.children

    x: implicitX
    y: implicitY

    // needed for the `mapToItem` function to work; apparently a Popup is not an Item
    Item
    {
        id: materialBrandSubMenuItem
        anchors.fill: parent
    }

    onOpened:
    {
        // we want to make sure here that the popup never goes out side the window so we adjust the x and y position
        // based on the width/height of the mainWindow/popup. QML is a bit weird here though, as the globalPosition
        // is in absolute coordinates relative to the origin of the mainWindow while setting the x and y coordinates
        // of the popup only changes the position relative to the parent.

        // reset position, the remainder of the function asumes this position and size
        materialBrandSubMenu.x = implicitX;
        materialBrandSubMenu.y = implicitY;
        materialBrandSubMenu.width = implicitWidth;
        materialBrandSubMenu.height = implicitHeight;

        const globalPosition = materialBrandSubMenuItem.mapToItem(null, 0, 0);

        if (globalPosition.y > mainWindow.height - materialBrandSubMenu.height)
        {
            if (mainWindow.height > materialBrandSubMenu.height)
            {
                const targetY = mainWindow.height - materialBrandSubMenu.height;
                const deltaY = globalPosition.y - targetY;
                materialBrandSubMenu.y = implicitY - deltaY;
            }
            else
            {
                // if popup is taller then the the component, limit
                // the components height and set the position to
                // y = 0 (in absolute coordinates)
                materialBrandSubMenu.y = implicitY - globalPosition.y;
                materialBrandSubMenu.height = mainWindow.height;
            }
        }

        // Changing the height causes implicitWidth to change because of the scrollbar appearing/disappearing
        // Reassign it here to update the value
        materialBrandSubMenu.width = implicitWidth;

        if (globalPosition.x > mainWindow.width - materialBrandSubMenu.width)
        {
            if (mainWindow.width > materialBrandSubMenu.width)
            {
                const targetX = mainWindow.width - materialBrandSubMenu.width;
                const deltaX = globalPosition.x - targetX;
                materialBrandSubMenu.x = implicitX - deltaX;
            }
            else
            {
                materialBrandSubMenu.x = implicitX - globalPosition.x;
                materialBrandSubMenu.width = mainWindow.width;
            }
        }
    }

    padding: background.border.width

    background: Rectangle
    {
        color: UM.Theme.getColor("main_background")
        border.color: UM.Theme.getColor("lining")
        border.width: UM.Theme.getSize("default_lining").width
    }

    ScrollView
    {
        id: scrollView
        anchors.fill: parent
        contentHeight: scrollViewContent.height
        clip: true

        ScrollBar.vertical: UM.ScrollBar
        {
            id: scrollbar
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
        }

        Rectangle
        {
            id: scrollViewContent
            width: childrenRect.width
            height: childrenRect.height
            color: UM.Theme.getColor("main_background")
        }
    }
}