// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import UM 1.4 as UM


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
    property bool packagesManageableInListView

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

        Label
        {
            id: sectionHeaderText
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left

            text: section
            font: UM.Theme.getFont("large")
            color: UM.Theme.getColor("text")
        }
    }

    ScrollBar.vertical: ScrollBar
    {
        // Vertical ScrollBar, styled similarly to the scrollBar in the settings panel
        id: verticalScrollBar
        visible: packages.contentHeight > packages.height

        background: Item{}

        contentItem: Rectangle
        {
            id: scrollViewHandle
            implicitWidth: UM.Theme.getSize("scrollbar").width
            radius: Math.round(implicitWidth / 2)
            color: verticalScrollBar.pressed ? UM.Theme.getColor("scrollbar_handle_down") : verticalScrollBar.hovered ? UM.Theme.getColor("scrollbar_handle_hover") : UM.Theme.getColor("scrollbar_handle")
            Behavior on color { ColorAnimation { duration: 50; } }
        }
    }

    delegate: MouseArea
    {
        id: cardMouseArea
        width: parent ? parent.width : 0
        height: childrenRect.height

        hoverEnabled: true
        onClicked:
        {
            packages.selectedPackage = model.package;
            contextStack.push(packageDetailsComponent);
        }

        PackageCard
        {
            manageableInListView: packages.packagesManageableInListView
            packageData: model.package
            width: parent.width - UM.Theme.getSize("default_margin").width - UM.Theme.getSize("narrow_margin").width
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
                    UM.RecolorImage
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
