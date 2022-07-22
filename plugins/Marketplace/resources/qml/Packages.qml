// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15

import UM 1.6 as UM


ListView
{
    id: packages
    width: parent.width

    property string pageTitle
    property var selectedPackage
    property string searchInBrowserUrl
    property bool bannerVisible
    property var bannerIcon
    property string bannerText
    property string bannerReadMoreUrl
    property var onRemoveBanner

    property bool showUpdateButton
    property bool showDisableButton
    property bool showInstallButton

    clip: true

    Component.onCompleted: model.updatePackages()
    Component.onDestruction: model.cleanUpAPIRequest()

    spacing: UM.Theme.getSize("default_margin").height

    section.property: "package.sectionTitle"
    section.delegate: Rectangle
    {
        width: packages.width
        height: sectionHeaderText.height + UM.Theme.getSize("default_margin").height

        color: UM.Theme.getColor("detail_background")

        UM.Label
        {
            id: sectionHeaderText
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left

            text: section
            font: UM.Theme.getFont("large")
        }
    }

    ScrollBar.vertical: UM.ScrollBar { id: verticalScrollBar }

    delegate: MouseArea
    {
        id: cardMouseArea
        width: parent ? parent.width : 0
        height: childrenRect.height

        hoverEnabled: true
        onClicked:
        {
            if (!model.package.isMissingPackageInformation)
            {
                packages.selectedPackage = model.package;
                contextStack.push(packageDetailsComponent);
            }
        }

        PackageCard
        {
            showUpdateButton: packages.showUpdateButton
            showDisableButton: packages.showDisableButton
            showInstallButton: packages.showInstallButton
            packageData: model.package
            width: {
                if (verticalScrollBar.visible)
                {
                    return parent.width - UM.Theme.getSize("default_margin").width - UM.Theme.getSize("default_margin").width
                }
                else
                {
                    return parent.width - UM.Theme.getSize("default_margin").width
                }
            }
            color: cardMouseArea.containsMouse ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("main_background")
        }
    }

    Component
    {
        id: packageDetailsComponent

        PackageDetails
        {
            packageData: packages.selectedPackage
            title: packages.pageTitle
        }
    }

    //Wrapper item to add spacing between content and footer.
    footer: Item
    {
        width: parent.width - UM.Theme.getSize("default_margin").width - UM.Theme.getSize("narrow_margin").width
        height: model.hasFooter || packages.model.errorMessage != "" ? UM.Theme.getSize("card").height + packages.spacing : 0
        visible: model.hasFooter || packages.model.errorMessage != ""
        Button
        {
            id: loadMoreButton
            width: parent.width
            height: UM.Theme.getSize("card").height
            anchors.bottom: parent.bottom

            enabled: packages.model.hasMore && !packages.model.isLoading || packages.model.errorMessage != ""
            onClicked: packages.model.updatePackages()  //Load next page in plug-in list.

            background: Rectangle
            {
                anchors.fill: parent
                radius: UM.Theme.getSize("default_radius").width
                color: UM.Theme.getColor("main_background")
            }

            Row
            {
                anchors.centerIn: parent

                spacing: UM.Theme.getSize("thin_margin").width

                states:
                [
                    State
                    {
                        name: "Error"
                        when: packages.model.errorMessage != ""
                        PropertyChanges
                        {
                            target: errorIcon
                            visible: true
                        }
                        PropertyChanges
                        {
                            target: loadMoreIcon
                            visible: false
                        }
                        PropertyChanges
                        {
                            target: loadMoreLabel
                            text: catalog.i18nc("@button", "Failed to load packages:") + " " + packages.model.errorMessage + "\n" + catalog.i18nc("@button", "Retry?")
                        }
                    },
                    State
                    {
                        name: "Loading"
                        when: packages.model.isLoading
                        PropertyChanges
                        {
                            target: loadMoreIcon
                            source: UM.Theme.getIcon("ArrowDoubleCircleRight")
                            color: UM.Theme.getColor("action_button_disabled_text")
                        }
                        PropertyChanges
                        {
                            target: loadMoreLabel
                            text: catalog.i18nc("@button", "Loading")
                            color: UM.Theme.getColor("action_button_disabled_text")
                        }
                    },
                    State
                    {
                        name: "LastPage"
                        when: !packages.model.hasMore
                        PropertyChanges
                        {
                            target: loadMoreIcon
                            visible: false
                        }
                        PropertyChanges
                        {
                            target: loadMoreLabel
                            text: packages.model.count > 0 ? catalog.i18nc("@message", "No more results to load") : catalog.i18nc("@message", "No results found with current filter")
                            color: UM.Theme.getColor("action_button_disabled_text")
                        }
                    }
                ]

                Item
                {
                    width: (errorIcon.visible || loadMoreIcon.visible) ? UM.Theme.getSize("small_button_icon").width : 0
                    height: UM.Theme.getSize("small_button_icon").height
                    anchors.verticalCenter: loadMoreLabel.verticalCenter

                    UM.StatusIcon
                    {
                        id: errorIcon
                        anchors.fill: parent

                        status: UM.StatusIcon.Status.ERROR
                        visible: false
                    }
                    UM.ColorImage
                    {
                        id: loadMoreIcon
                        anchors.fill: parent

                        source: UM.Theme.getIcon("ArrowDown")
                        color: UM.Theme.getColor("secondary_button_text")

                        RotationAnimator
                        {
                            target: loadMoreIcon
                            from: 0
                            to: 360
                            duration: 1000
                            loops: Animation.Infinite
                            running: packages.model.isLoading
                            alwaysRunToEnd: true
                        }
                    }
                }
                Label
                {
                    id: loadMoreLabel
                    text: catalog.i18nc("@button", "Load more")
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("secondary_button_text")
                }
            }
        }
    }
}
