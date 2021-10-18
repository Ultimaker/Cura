// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.15

import UM 1.4 as UM
import Cura 1.1 as Cura

Popup
{
    id: applicationSwitcherPopup

    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutsideParent

    opacity: opened ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 100 } }
    padding: UM.Theme.getSize("wide_margin").width

    contentItem: Grid
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
                    description: catalog.i18nc("@tooltip:button", "Monitor printers in Ultimaker Digital Factory."),
                    link: "https://digitalfactory.ultimaker.com/app/printers?utm_source=cura&utm_medium=software&utm_campaign=switcher-digital-factory-printers",
                    DFAccessRequired: true
                },
                {
                    displayName: "Digital Library", //Not translated, since it's a brand name.
                    thumbnail: UM.Theme.getIcon("Library", "high"),
                    description: catalog.i18nc("@tooltip:button", "Create print projects in Digital Library."),
                    link: "https://digitalfactory.ultimaker.com/app/library?utm_source=cura&utm_medium=software&utm_campaign=switcher-library",
                    DFAccessRequired: true
                },
                {
                    displayName: catalog.i18nc("@label:button", "Print jobs"),
                    thumbnail: UM.Theme.getIcon("FoodBeverages"),
                    description: catalog.i18nc("@tooltip:button", "Monitor print jobs and reprint from your print history."),
                    link: "https://digitalfactory.ultimaker.com/app/print-jobs?utm_source=cura&utm_medium=software&utm_campaign=switcher-digital-factory-printjobs",
                    DFAccessRequired: true
                },
                {
                    displayName: "Ultimaker Marketplace", //Not translated, since it's a brand name.
                    thumbnail: UM.Theme.getIcon("Shop", "high"),
                    description: catalog.i18nc("@tooltip:button", "Extend Ultimaker Cura with plugins and material profiles."),
                    link: "https://marketplace.ultimaker.com/?utm_source=cura&utm_medium=software&utm_campaign=switcher-marketplace-materials",
                    DFAccessRequired: false
                },
                {
                    displayName: "Ultimaker Academy", //Not translated, since it's a brand name.
                    thumbnail: UM.Theme.getIcon("Knowledge"),
                    description: catalog.i18nc("@tooltip:button", "Become a 3D printing expert with Ultimaker e-learning."),
                    link: "https://academy.ultimaker.com/?utm_source=cura&utm_medium=software&utm_campaign=switcher-academy",
                    DFAccessRequired: false
                },
                {
                    displayName: catalog.i18nc("@label:button", "Ultimaker support"),
                    thumbnail: UM.Theme.getIcon("Help", "high"),
                    description: catalog.i18nc("@tooltip:button", "Learn how to get started with Ultimaker Cura."),
                    link: "https://support.ultimaker.com/?utm_source=cura&utm_medium=software&utm_campaign=switcher-support",
                    DFAccessRequired: false
                },
                {
                    displayName: catalog.i18nc("@label:button", "Ask a question"),
                    thumbnail: UM.Theme.getIcon("Speak", "high"),
                    description: catalog.i18nc("@tooltip:button", "Consult the Ultimaker Community."),
                    link: "https://community.ultimaker.com/?utm_source=cura&utm_medium=software&utm_campaign=switcher-community",
                    DFAccessRequired: false
                },
                {
                    displayName: catalog.i18nc("@label:button", "Report a bug"),
                    thumbnail: UM.Theme.getIcon("Bug", "high"),
                    description: catalog.i18nc("@tooltip:button", "Let developers know that something is going wrong."),
                    link: "https://github.com/Ultimaker/Cura/issues/new/choose",
                    DFAccessRequired: false
                },
                {
                    displayName: "Ultimaker.com", //Not translated, since it's a URL.
                    thumbnail: UM.Theme.getIcon("Browser"),
                    description: catalog.i18nc("@tooltip:button", "Visit the Ultimaker website."),
                    link: "https://ultimaker.com/?utm_source=cura&utm_medium=software&utm_campaign=switcher-umwebsite",
                    DFAccessRequired: false
                }
            ]

            delegate: ApplicationButton
            {
                displayName: modelData.displayName
                iconSource: modelData.thumbnail
                tooltipText: modelData.description
                isExternalLink: true
                visible: modelData.DFAccessRequired ? Cura.API.account.isLoggedIn & Cura.API.account.additionalRights["df_access"] : true

                onClicked: Qt.openUrlExternally(modelData.link)
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
