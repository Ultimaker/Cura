// Copyright (C) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Window 2.2
import QtQuick.Controls 1.4 as OldControls // TableView doesn't exist in the QtQuick Controls 2.x in 5.10, so use the old one
import QtQuick.Controls 2.3
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.1

import UM 1.2 as UM
import Cura 1.6 as Cura

import DigitalFactory 1.0 as DF


Item
{
    id: base

    width: parent.width
    height: parent.height
    property bool createNewProjectButtonVisible: true

    anchors
    {
        top: parent.top
        bottom: parent.bottom
        left: parent.left
        right: parent.right
        margins: UM.Theme.getSize("default_margin").width
    }

    RowLayout
    {
        id: headerRow

        anchors
        {
            top: parent.top
            left: parent.left
            right: parent.right
        }
        height: childrenRect.height
        spacing: UM.Theme.getSize("default_margin").width

        Cura.TextField
        {
            id: searchBar
            Layout.fillWidth: true
            implicitHeight: createNewProjectButton.height
            leftPadding: searchIcon.width + UM.Theme.getSize("default_margin").width * 2

            onTextEdited: manager.projectFilter = text //Update the search filter when editing this text field.

            placeholderText: "Search"

            UM.RecolorImage
            {
                id: searchIcon

                anchors
                {
                    verticalCenter: parent.verticalCenter
                    left: parent.left
                    leftMargin: UM.Theme.getSize("default_margin").width
                }
                source: UM.Theme.getIcon("search")
                height: UM.Theme.getSize("small_button_icon").height
                width: height
                color: UM.Theme.getColor("text")
            }
        }

        Cura.SecondaryButton
        {
            id: createNewProjectButton

            text: "New Library project"
            visible: createNewProjectButtonVisible && manager.userAccountCanCreateNewLibraryProject && (manager.retrievingProjectsStatus == DF.RetrievalStatus.Success || manager.retrievingProjectsStatus == DF.RetrievalStatus.Failed)

            onClicked:
            {
                createNewProjectPopup.open()
            }
            busy: manager.creatingNewProjectStatus == DF.RetrievalStatus.InProgress
        }


        Cura.SecondaryButton
        {
            id: upgradePlanButton

            text: "Upgrade plan"
            iconSource: UM.Theme.getIcon("external_link")
            visible: createNewProjectButtonVisible && !manager.userAccountCanCreateNewLibraryProject && (manager.retrievingProjectsStatus == DF.RetrievalStatus.Success || manager.retrievingProjectsStatus == DF.RetrievalStatus.Failed)
            tooltip: "Maximum number of projects reached. Please upgrade your subscription to create more projects."

            onClicked: Qt.openUrlExternally("https://ultimaker.com/software/enterprise-software?utm_source=cura&utm_medium=software&utm_campaign=MaxProjLink")
        }
    }

    Item
    {
        id: noLibraryProjectsContainer
        anchors
        {
            top: parent.top
            bottom: parent.bottom
            left: parent.left
            right: parent.right
        }
        visible: manager.digitalFactoryProjectModel.count == 0 && (manager.retrievingProjectsStatus == DF.RetrievalStatus.Success || manager.retrievingProjectsStatus == DF.RetrievalStatus.Failed)

        Column
        {
            anchors.centerIn: parent
            spacing: UM.Theme.getSize("thin_margin").height
            Image
            {
                id: digitalFactoryImage
                anchors.horizontalCenter: parent.horizontalCenter
                source: searchBar.text === "" ? "../images/digital_factory.svg" : "../images/projects_not_found.svg"
                fillMode: Image.PreserveAspectFit
                width: parent.width - 2 * UM.Theme.getSize("thick_margin").width
            }

            Label
            {
                id: noLibraryProjectsLabel
                anchors.horizontalCenter: parent.horizontalCenter
                text: searchBar.text === "" ? "It appears that you don't have any projects in the Library yet." : "No projects found that match the search query."
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text")
            }

            Cura.TertiaryButton
            {
                id: visitDigitalLibraryButton
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Visit Digital Library"
                onClicked:  Qt.openUrlExternally(CuraApplication.ultimakerDigitalFactoryUrl + "/app/library?utm_source=cura&utm_medium=software&utm_campaign=empty-library")
                visible: searchBar.text === "" //Show the link to Digital Library when there are no projects in the user's Library.
            }
        }
    }

    Item
    {
        id: projectListContainer
        anchors
        {
            top: headerRow.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            bottom: parent.bottom
            left: parent.left
            right: parent.right
        }
        visible: manager.digitalFactoryProjectModel.count > 0

        // Use a flickable and a column with a repeater instead of a ListView in a ScrollView, because the ScrollView cannot
        // have additional children (aside from the view inside it), which wouldn't allow us to add the LoadMoreProjectsCard
        // in it.
        Flickable
        {
            id: flickableView
            clip: true
            contentWidth: parent.width
            contentHeight: projectsListView.implicitHeight
            anchors.fill: parent

            ScrollBar.vertical: ScrollBar
            {
                // Vertical ScrollBar, styled similarly to the scrollBar in the settings panel
                id: verticalScrollBar
                visible: flickableView.contentHeight > flickableView.height

                background: Rectangle
                {
                    implicitWidth: UM.Theme.getSize("scrollbar").width
                    radius: Math.round(implicitWidth / 2)
                    color: UM.Theme.getColor("scrollbar_background")
                }

                contentItem: Rectangle
                {
                    id: scrollViewHandle
                    implicitWidth: UM.Theme.getSize("scrollbar").width
                    radius: Math.round(implicitWidth / 2)

                    color: verticalScrollBar.pressed ? UM.Theme.getColor("scrollbar_handle_down") : verticalScrollBar.hovered ? UM.Theme.getColor("scrollbar_handle_hover") : UM.Theme.getColor("scrollbar_handle")
                    Behavior on color { ColorAnimation { duration: 50; } }
                }
            }

            Column
            {
                id: projectsListView
                width: verticalScrollBar.visible ? parent.width - verticalScrollBar.width - UM.Theme.getSize("default_margin").width : parent.width
                anchors.top: parent.top
                spacing: UM.Theme.getSize("narrow_margin").width

                Repeater
                {
                    model: manager.digitalFactoryProjectModel
                    delegate: ProjectSummaryCard
                    {
                        id: projectSummaryCard
                        imageSource: model.thumbnailUrl || "../images/placeholder.svg"
                        projectNameText: model.displayName
                        projectUsernameText: model.username
                        projectLastUpdatedText: "Last updated: " + model.lastUpdated

                        onClicked:
                        {
                            manager.selectedProjectIndex = index
                        }
                    }
                }

                LoadMoreProjectsCard
                {
                    id: loadMoreProjectsCard
                    height: UM.Theme.getSize("toolbox_thumbnail_small").height
                    width: parent.width
                    visible: manager.digitalFactoryProjectModel.count > 0
                    hasMoreProjectsToLoad: manager.hasMoreProjectsToLoad

                    onClicked:
                    {
                        manager.loadMoreProjects()
                    }
                }
            }
        }
    }

    CreateNewProjectPopup
    {
        id: createNewProjectPopup
        width: 400 * screenScaleFactor
        height: 220 * screenScaleFactor
        x: Math.round((parent.width - width) / 2)
        y: Math.round((parent.height - height) / 2)
    }
}