//Copyright (C) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Window 2.2
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.7 as Cura

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

        Cura.SearchBar
        {
            id: searchBar
            Layout.fillWidth: true
            implicitHeight: createNewProjectButton.height
            focus: true
            onTextEdited: manager.projectFilter = text //Update the search filter when editing this text field.
        }

        Cura.SecondaryButton
        {
            id: createNewProjectButton

            text: "New Library project"
            visible: createNewProjectButtonVisible && manager.userAccountCanCreateNewLibraryProject && (manager.retrievingProjectsStatus == 2 || manager.retrievingProjectsStatus == 3) // Status is succeeded or failed

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
                source: Qt.resolvedUrl(searchBar.text === "" ? "../images/digital_factory.svg" : "../images/projects_not_found.svg")
                fillMode: Image.PreserveAspectFit
                width: parent.width - 2 * UM.Theme.getSize("thick_margin").width
            }

            UM.Label
            {
                id: noLibraryProjectsLabel
                anchors.horizontalCenter: parent.horizontalCenter
                text: searchBar.text === "" ? "It appears that you don't have any projects in the Library yet." : "No projects found that match the search query."
                font: UM.Theme.getFont("medium")
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

            ScrollBar.vertical: UM.ScrollBar { id: verticalScrollBar }

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
                    height: UM.Theme.getSize("card_icon").height
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
