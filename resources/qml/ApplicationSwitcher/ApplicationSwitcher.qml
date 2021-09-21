// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.15

import UM 1.4 as UM
import Cura 1.1 as Cura

Item
{
    id: applicationSwitcherWidget
    width: applicationSwitcherButton.width
    height: width

    Button
    {
        id: applicationSwitcherButton
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter

        width: Math.round(0.5 * UM.Theme.getSize("main_window_header").height)
        height: width

        background: Item
        {
            anchors.fill: parent

            Rectangle
            {
                anchors.fill: parent
                radius: UM.Theme.getSize("action_button_radius").width
                color: applicationSwitcherButton.hovered ? UM.Theme.getColor("primary_text") : "transparent"
                opacity: applicationSwitcherButton.hovered ? 0.2 : 0
            }

            UM.RecolorImage
            {
                anchors.fill: parent
                color: UM.Theme.getColor("primary_text")

                source: UM.Theme.getIcon("BlockGrid")
            }
        }

        onClicked:
        {
            if (applicationSwitcherPopup.opened)
            {
                applicationSwitcherPopup.close()
            } else {
                applicationSwitcherPopup.open()
            }
        }
    }

    Popup
    {
        id: applicationSwitcherPopup

        y: parent.height + UM.Theme.getSize("default_arrow").height

        // Move the x position by the default margin so that the arrow isn't drawn exactly on the corner
        x: parent.width - width + UM.Theme.getSize("default_margin").width

        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

        opacity: opened ? 1 : 0
        Behavior on opacity { NumberAnimation { duration: 100 } }
        padding: 0
        width: contentWidth + 2 * UM.Theme.getSize("wide_margin").width
        height: contentHeight + 2 * UM.Theme.getSize("wide_margin").width

        contentItem: Item
        {
            id: applicationsContainer
            anchors.fill: parent
            anchors.margins: UM.Theme.getSize("wide_margin").width

            Column
            {
                id: contentsColumn
                anchors.top: parent.top
                anchors.left: parent.left

                width: ultimakerPlatformLinksGrid.width

                Grid
                {
                    id: ultimakerPlatformLinksGrid
                    columns: 3
                    spacing: UM.Theme.getSize("default_margin").width

                    Repeater
                    {
                        model:
                        [
                            { displayName: "Report issue1", thumbnail: UM.Theme.getIcon("Bug"), description: "This is the description1", link: "https://github.com/Ultimaker/Cura/issues/1" },
                            { displayName: "My printers", thumbnail: UM.Theme.getIcon("Bug"), description: "This is the description2", link: "https://github.com/Ultimaker/Cura/issues/2" },
                            { displayName: "Ultimaker.com", thumbnail: UM.Theme.getIcon("Bug"), description: "This is the description3", link: "https://ultimaker.com" },
                            { displayName: "Report issue4", thumbnail: UM.Theme.getIcon("Bug"), description: "This is the description4", link: "https://github.com/Ultimaker/Cura/issues/4" },
                            { displayName: "Report issue5", thumbnail: UM.Theme.getIcon("Bug"), description: "This is the description5", link: "https://github.com/Ultimaker/Cura/issues/5" }
                        ]

                        delegate: ApplicationButton
                        {
                            displayName: modelData.displayName
                            iconSource: modelData.thumbnail
                            tooltipText: modelData.description
                            isExternalLink: true

                            onClicked: Qt.openUrlExternally(modelData.link)
                        }
                    }
                }
            }

        }

        background: UM.PointingRectangle
        {
            color: UM.Theme.getColor("tool_panel_background")
            borderColor: UM.Theme.getColor("lining")
            borderWidth: UM.Theme.getSize("default_lining").width

            // Move the target by the default margin so that the arrow isn't drawn exactly on the corner
            target: Qt.point(width - UM.Theme.getSize("default_margin").width - (applicationSwitcherButton.width / 2), -10)

            arrowSize: UM.Theme.getSize("default_arrow").width
        }
    }
}