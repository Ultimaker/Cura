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

    property var fileModel: manager.digitalFactoryFileModel

    signal openFilePressed()
    signal selectDifferentProjectPressed()

    anchors
    {
        fill: parent
        margins: UM.Theme.getSize("default_margin").width
    }

    ProjectSummaryCard
    {
        id: projectSummaryCard

        anchors.top: parent.top

        property var selectedItem: manager.digitalFactoryProjectModel.getItem(manager.selectedProjectIndex)
        
        imageSource: selectedItem.thumbnailUrl || "../images/placeholder.svg"
        projectNameText: selectedItem.displayName || ""
        projectUsernameText: selectedItem.username || ""
        projectLastUpdatedText: "Last updated: " + selectedItem.lastUpdated
        cardMouseAreaEnabled: false
    }
    
    Rectangle
    {
        id: projectFilesContent
        width: parent.width
        anchors.top: projectSummaryCard.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").width
        anchors.bottom: selectDifferentProjectButton.top
        anchors.bottomMargin: UM.Theme.getSize("default_margin").width

        color: UM.Theme.getColor("main_background")
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")


        Cura.TableView
        {
            id: filesTableView
            anchors.fill: parent
            model: manager.digitalFactoryFileModel
            visible: model.count != 0 && manager.retrievingFileStatus != DF.RetrievalStatus.InProgress
            selectionMode: OldControls.SelectionMode.SingleSelection
            onDoubleClicked:
            {
                manager.setSelectedFileIndices([row]);
                openFilesButton.clicked();
            }

            OldControls.TableViewColumn
            {
                id: fileNameColumn
                role: "fileName"
                title: "Name"
                width: Math.round(filesTableView.width / 3)
            }

            OldControls.TableViewColumn
            {
                id: usernameColumn
                role: "username"
                title: "Uploaded by"
                width: Math.round(filesTableView.width / 3)
            }

            OldControls.TableViewColumn
            {
                role: "uploadedAt"
                title: "Uploaded at"
            }

            Connections
            {
                target: filesTableView.selection
                function onSelectionChanged()
                {
                    let newSelection = [];
                    filesTableView.selection.forEach(function(rowIndex) { newSelection.push(rowIndex); });
                    manager.setSelectedFileIndices(newSelection);
                }
            }
        }

        Label
        {
            id: emptyProjectLabel
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            text: "Select a project to view its files."
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("setting_category_text")

            Connections
            {
                target: manager
                function onSelectedProjectIndexChanged(newProjectIndex)
                {
                    emptyProjectLabel.visible = (newProjectIndex == -1)
                }
            }
        }

        Label
        {
            id: noFilesInProjectLabel
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            visible: (manager.digitalFactoryFileModel.count == 0 && !emptyProjectLabel.visible && !retrievingFilesBusyIndicator.visible)
            text: "No supported files in this project."
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("setting_category_text")
        }

        BusyIndicator
        {
            // Shows up while Cura is waiting to receive the files of a project from the digital factory library
            id: retrievingFilesBusyIndicator

            anchors
            {
                verticalCenter: parent.verticalCenter
                horizontalCenter: parent.horizontalCenter
            }

            width: parent.width / 4
            height: width
            visible: manager.retrievingFilesStatus == DF.RetrievalStatus.InProgress
            running: visible
            palette.dark: UM.Theme.getColor("text")
        }

        Connections
        {
            target: manager.digitalFactoryFileModel

            function onItemsChanged()
            {
                // Make sure no files are selected when the file model changes
                filesTableView.currentRow = -1
                filesTableView.selection.clear()
            }
        }
    }
    Cura.SecondaryButton
    {
        id: selectDifferentProjectButton

        anchors.bottom: parent.bottom
        anchors.left: parent.left
        text: "Change Library project"

        onClicked:
        {
            manager.clearProjectSelection()
        }
        busy: false
    }

    Cura.PrimaryButton
    {
        id: openFilesButton

        anchors.bottom: parent.bottom
        anchors.right: parent.right
        text: "Open"
        enabled: filesTableView.selection.count > 0
        onClicked:
        {
            manager.openSelectedFiles()
        }
        busy: false
    }

    Component.onCompleted:
    {
        openFilesButton.clicked.connect(base.openFilePressed)
        selectDifferentProjectButton.clicked.connect(base.selectDifferentProjectPressed)
    }
}