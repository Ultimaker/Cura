// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.4
import QtQuick.Layouts 2.7

import UM 1.5 as UM
import Cura 1.7 as Cura

/* This element is a workaround for MacOS, where it can crash in Qt6 when nested menus are closed.
Instead we'll use a pop-up which doesn't seem to have that problem. */

Cura.MenuItem
{
    id: materialBrandMenu
    overrideShowArrow: true

    property var materialTypesModel
    text: materialTypesModel.name

    contentItem: MouseArea
    {
        hoverEnabled: true

        RowLayout
        {
            spacing: 0
            opacity: materialBrandMenu.enabled ? 1 : 0.5

            Item
            {
                // Spacer
                width: UM.Theme.getSize("default_margin").width
            }

            UM.Label
            {
                text: replaceText(materialBrandMenu.text)
                Layout.fillWidth: true
                Layout.fillHeight:true
                elide: Label.ElideRight
                wrapMode: Text.NoWrap
            }

            Item
            {
                Layout.fillWidth: true
            }

            Item
            {
                // Right side margin
                width: UM.Theme.getSize("default_margin").width
            }
        }

        onEntered: showTimer.restartTimer()
        onExited: hideTimer.restartTimer()
    }

    Timer
    {
        id: showTimer
        interval: 100
        function restartTimer()
        {
            restart();
            running = Qt.binding(function() { return materialBrandMenu.enabled && materialBrandMenu.contentItem.containsMouse; });
            hideTimer.running = false;
        }
        onTriggered: menuPopup.open()
    }
    Timer
    {
        id: hideTimer
        interval: 250
        function restartTimer() //Restart but re-evaluate the running property then.
        {
            restart();
            running = Qt.binding(function() { return materialBrandMenu.enabled && !materialBrandMenu.contentItem.containsMouse && !menuPopup.itemHovered > 0; });
            showTimer.running = false;
        }
        onTriggered: menuPopup.close()
    }

    Popup
    {
        id: menuPopup
        x: parent.width
        y: 0
        width: materialTypesList.width + padding * 2
        height: materialTypesList.height + padding * 2

        padding: background.border.width
        // Nasty hack to ensure that we can keep track if the popup contains the mouse.
        // Since we also want a hover for the sub items (and these events are sent async)
        // We have to keep a count of itemHovered (instead of just a bool)
        property int itemHovered: 0
        MouseArea
        {
            id: submenuArea
            anchors.fill: parent

            hoverEnabled: true
            onEntered: hideTimer.restartTimer()
        }

        background: Rectangle
        {
            color: UM.Theme.getColor("main_background")
            border.color: UM.Theme.getColor("lining")
            border.width: UM.Theme.getSize("default_lining").width
        }

        Column
        {
            id: materialTypesList

            Repeater
            {
                model: materialTypesModel.material_types

                //Use a MouseArea and Rectangle, not a button, because the button grabs mouse events which makes the parent pop-up think it's no longer being hovered.
                //With a custom MouseArea, we can prevent the events from being accepted.
                delegate: Item
                {
                    width: materialTypeLabel.width
                    height: materialTypeLabel.height

                    Rectangle
                    {
                        width: materialTypesList.width
                        height: parent.height

                        color: materialTypeButton.containsMouse ? UM.Theme.getColor("background_2") : UM.Theme.getColor("background_1")

                        MouseArea
                        {
                            id: materialTypeButton
                            anchors.fill: parent
                            hoverEnabled: true

                            onEntered: menuPopup.itemHovered += 1
                            onExited: menuPopup.itemHovered -= 1
                        }
                    }

                    UM.Label
                    {
                        id: materialTypeLabel
                        text: model.name
                    }
                }
            }
        }
    }
}
