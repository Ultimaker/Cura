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
    width: Math.round(0.5 * UM.Theme.getSize("main_window_header").height)
    height: width

    Button
    {
        id: applicationSwitcherButton

        anchors.fill: parent

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
                            {
                                displayName: catalog.i18nc("@label:button", "My printers"),
                                thumbnail: UM.Theme.getIcon("PrinterTriple", "high"),
                                description: catalog.i18nc("@tooltip:button", "Manage your printers in the Digital Factory."),
                                link: "https://digitalfactory.ultimaker.com/app/printers?utm_source=cura&utm_medium=software&utm_campaign=switcher-digital-factory-printers"
                            },
                            {
                                displayName: "Digital Library", //Not translated, since it's a brand name.
                                thumbnail: UM.Theme.getIcon("Library", "high"),
                                description: catalog.i18nc("@tooltip:button", "Manage your files in the Digital Library."),
                                link: "https://digitalfactory.ultimaker.com/app/library?utm_source=cura&utm_medium=software&utm_campaign=switcher-library"
                            },
                            {
                                displayName: catalog.i18nc("@label:button", "Print jobs"),
                                thumbnail: UM.Theme.getIcon("FoodBeverages"),
                                description: catalog.i18nc("@tooltip:button", "Manage things that are being printed."),
                                link: "https://digitalfactory.ultimaker.com/app/print-jobs?utm_source=cura&utm_medium=software&utm_campaign=switcher-digital-factory- printjobs"
                            },
                            {
                                displayName: "Ultimaker Marketplace", //Not translated, since it's a brand name.
                                thumbnail: UM.Theme.getIcon("Shop", "high"),
                                description: catalog.i18nc("@tooltip:button", "Extend Ultimaker Cura with new plug-ins and profiles."),
                                link: "https://marketplace.ultimaker.com/?utm_source=cura&utm_medium=software&utm_campaign=switcher-marketplace-materials"
                            },
                            {
                                displayName: "Ultimaker Academy", //Not translated, since it's a brand name.
                                thumbnail: UM.Theme.getIcon("Knowledge"),
                                description: catalog.i18nc("@tooltip:button", "Become an expert in 3D printing."),
                                link: "https://academy.ultimaker.com/?utm_source=cura&utm_medium=software&utm_campaign=switcher-academy"
                            },
                            {
                                displayName: catalog.i18nc("@label:button", "Ultimaker support"),
                                thumbnail: UM.Theme.getIcon("Help", "high"),
                                description: catalog.i18nc("@tooltip:button", "Get help with how to use Ultimaker Cura."),
                                link: "https://support.ultimaker.com/?utm_source=cura&utm_medium=software&utm_campaign=switcher-support"
                            },
                            {
                                displayName: catalog.i18nc("@label:button", "Ask a question"),
                                thumbnail: UM.Theme.getIcon("Speak", "high"),
                                description: catalog.i18nc("@tooltip:button", "Consult the Ultimaker community."),
                                link: "https://community.ultimaker.com/?utm_source=cura&utm_medium=software&utm_campaign=switcher-community"
                            },
                            {
                                displayName: catalog.i18nc("@label:button", "Report a bug"),
                                thumbnail: UM.Theme.getIcon("Bug", "high"),
                                description: catalog.i18nc("@tooltip:button", "Notify the developers that something is going wrong."),
                                link: "https://github.com/Ultimaker/Cura/issues/new/choose"
                            },
                            {
                                displayName: "Ultimaker.com", //Not translated, since it's a URL.
                                thumbnail: UM.Theme.getIcon("Browser"),
                                description: catalog.i18nc("@tooltip:button", "Visit Ultimaker's website."),
                                link: "https://ultimaker.com/?utm_source=cura&utm_medium=software&utm_campaign=switcher-umwebsite"
                            }
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