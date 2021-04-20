// Copyright (C) 2021 Ultimaker B.V.

import QtQuick 2.10
import QtQuick.Window 2.2
import QtQuick.Controls 1.4 as OldControls // TableView doesn't exist in the QtQuick Controls 2.x in 5.10, so use the old one
import QtQuick.Controls 2.3
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.6 as Cura

import DigitalFactory 1.0 as DF


Item
{
    id: base

    width: parent.width
    height: parent.height
    property alias createNewProjectButtonVisible: createNewProjectButton.visible

    anchors
    {
        top: parent.top
        bottom: parent.bottom
        left: parent.left
        right: parent.right
        margins: UM.Theme.getSize("default_margin").width
    }

    Label
    {
        id: selectProjectLabel

        text: "Select Project"
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("small_button_text")
        anchors.top: parent.top
        anchors.left: parent.left
        visible: projectListContainer.visible
    }

    Cura.SecondaryButton
    {
        id: createNewProjectButton

        anchors.verticalCenter: selectProjectLabel.verticalCenter
        anchors.right: parent.right
        text: "New Library project"

        onClicked:
        {
            createNewProjectPopup.open()
        }
        busy: manager.creatingNewProjectStatus == DF.RetrievalStatus.InProgress
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
                source: "../images/digital_factory.svg"
                fillMode: Image.PreserveAspectFit
                width: parent.width - 2 * UM.Theme.getSize("thick_margin").width
                sourceSize.width: width
                sourceSize.height: height
            }

            Label
            {
                id: noLibraryProjectsLabel
                anchors.horizontalCenter: parent.horizontalCenter
                text: "It appears that you don't have any projects in the Library yet."
                font: UM.Theme.getFont("medium")
            }

            Cura.TertiaryButton
            {
                id: visitDigitalLibraryButton
                anchors.horizontalCenter: parent.horizontalCenter
                text: "Visit Digital Library"
                onClicked:  Qt.openUrlExternally(CuraApplication.ultimakerDigitalFactoryUrl + "/app/library")
            }
        }
    }

    Item
    {
        id: projectListContainer
        anchors
        {
            top: selectProjectLabel.bottom
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