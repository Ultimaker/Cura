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

    signal savePressed()
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

    Label
    {
        id: fileNameLabel
        anchors.top: projectSummaryCard.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        text: "Cura project name"
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("text")
    }


    Cura.TextField
    {
        id: dfFilenameTextfield
        width: parent.width
        anchors.left: parent.left
        anchors.top: fileNameLabel.bottom
        anchors.topMargin: UM.Theme.getSize("thin_margin").height
        validator: RegExpValidator
        {
            regExp: /^[\w\-\. ()]{0,255}$/
        }

        text: PrintInformation.jobName
        font: UM.Theme.getFont("medium")
        placeholderText: "Enter the name of the file."
        onAccepted: { if (saveButton.enabled) {saveButton.clicked()}}
    }


    Rectangle
    {
        id: projectFilesContent
        width: parent.width
        anchors.top: dfFilenameTextfield.bottom
        anchors.topMargin: UM.Theme.getSize("wide_margin").height
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
            selectionMode: OldControls.SelectionMode.NoSelection

            OldControls.TableViewColumn
            {
                id: fileNameColumn
                role: "fileName"
                title: "@tableViewColumn:title", "Name"
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
                function onSelectedProjectIndexChanged()
                {
                    emptyProjectLabel.visible = (manager.newProjectIndex == -1)
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
            manager.selectedProjectIndex = -1
        }
        busy: false
    }

    Cura.PrimaryButton
    {
        id: saveButton

        anchors.bottom: parent.bottom
        anchors.right: parent.right
        text: "Save"
        enabled: (asProjectCheckbox.checked || asSlicedCheckbox.checked) && dfFilenameTextfield.text.length >= 1 && dfFilenameTextfield.state !== 'invalid'

        onClicked:
        {
            let saveAsFormats = [];
            if (asProjectCheckbox.checked)
            {
                saveAsFormats.push("3mf");
            }
            if (asSlicedCheckbox.checked)
            {
                saveAsFormats.push("ufp");
            }
            manager.saveFileToSelectedProject(dfFilenameTextfield.text, saveAsFormats);
        }
        busy: false
    }

    Row
    {

        id: saveAsFormatRow
        anchors.verticalCenter: saveButton.verticalCenter
        anchors.right: saveButton.left
        anchors.rightMargin: UM.Theme.getSize("thin_margin").height
        width: childrenRect.width
        spacing: UM.Theme.getSize("default_margin").width

        Cura.CheckBox
        {
            id: asProjectCheckbox
            height: UM.Theme.getSize("checkbox").height
            anchors.verticalCenter: parent.verticalCenter
            checked: true
            text: "Save Cura project"
            font: UM.Theme.getFont("medium")
        }

        Cura.CheckBox
        {
            id: asSlicedCheckbox
            height: UM.Theme.getSize("checkbox").height
            anchors.verticalCenter: parent.verticalCenter

            enabled: UM.Backend.state == UM.Backend.Done
            checked: UM.Backend.state == UM.Backend.Done
            text: "Save print file"
            font: UM.Theme.getFont("medium")
        }
    }

    Component.onCompleted:
    {
        saveButton.clicked.connect(base.savePressed)
        selectDifferentProjectButton.clicked.connect(base.selectDifferentProjectPressed)
    }
}
