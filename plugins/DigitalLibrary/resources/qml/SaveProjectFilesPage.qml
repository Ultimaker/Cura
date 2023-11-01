//Copyright (C) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Window 2.2
import QtQuick.Controls 2.3

import UM 1.6 as UM
import Cura 1.6 as Cura

import DigitalFactory 1.0 as DF


Item
{
    id: base

    property variant catalog: UM.I18nCatalog { name: "cura" }

    width: parent.width
    height: parent.height

    property var fileModel: manager.digitalFactoryFileModel
    property var modelRows: manager.digitalFactoryFileModel.items

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

    UM.Label
    {
        id: fileNameLabel
        anchors.top: projectSummaryCard.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        text: "Cura project name"
        font: UM.Theme.getFont("medium")
    }


    Cura.TextField
    {
        id: dfFilenameTextfield
        width: parent.width
        anchors.left: parent.left
        anchors.top: fileNameLabel.bottom
        anchors.topMargin: UM.Theme.getSize("thin_margin").height
        validator: RegularExpressionValidator
        {
            regularExpression: /^[\w\-\. ()]{0,255}$/
        }

        text: PrintInformation.jobName
        font: fontMetrics.font
        height: fontMetrics.height + 2 * UM.Theme.getSize("thin_margin").height
        placeholderText: "Enter the name of the file."
        onAccepted: { if (saveButton.enabled) {saveButton.clicked()}}
    }

    FontMetrics
    {
        id: fontMetrics
        font: UM.Theme.getFont("medium")
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

        // This is not backwards compatible with Cura < 5.0 due to QT.labs being removed in PyQt6
        Cura.TableView
        {
            id: filesTableView
            anchors.fill: parent
            anchors.margins: parent.border.width

            allowSelection: false
            columnHeaders: ["Name", "Uploaded by", "Uploaded at"]
            model: UM.TableModel
            {
                id: tableModel
                headers: ["fileName", "username", "uploadedAt"]
                rows: manager.digitalFactoryFileModel.items
            }
        }

        UM.Label
        {
            id: emptyProjectLabel
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            text: "Select a project to view its files."
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

        UM.Label
        {
            id: noFilesInProjectLabel
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            visible: (manager.digitalFactoryFileModel.count == 0 && !emptyProjectLabel.visible && !retrievingFilesBusyIndicator.visible)
            text: "No supported files in this project."
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
                filesTableView.currentRow = -1;
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

        onClicked: manager.saveFileToSelectedProject(dfFilenameTextfield.text, asProjectComboBox.currentValue)
        busy: false
    }

    Cura.ComboBox
    {
        id: asProjectComboBox

        width: UM.Theme.getSize("combobox_wide").width
        height: saveButton.height
        anchors.verticalCenter: saveButton.verticalCenter
        anchors.right: saveButton.left
        anchors.rightMargin: UM.Theme.getSize("thin_margin").height

        enabled: UM.Backend.state == UM.Backend.Done
        currentIndex: UM.Backend.state == UM.Backend.Done ? dfFilenameTextfield.text.startsWith("MM")? 1 : 0 : 2

        textRole: "text"
        valueRole: "value"

        model: [
            { text: catalog.i18nc("@option", "Save Cura project and .ufp print file"), key: "3mf_ufp", value: ["3mf", "ufp"] },
            { text: catalog.i18nc("@option", "Save Cura project and .makerbot print file"), key: "3mf_makerbot", value: ["3mf", "makerbot"] },
            { text: catalog.i18nc("@option", "Save Cura project"), key: "3mf", value: ["3mf"] },
        ]
    }

    Component.onCompleted:
    {
        saveButton.clicked.connect(base.savePressed)
        selectDifferentProjectButton.clicked.connect(base.selectDifferentProjectPressed)
    }

    onModelRowsChanged:
    {
        tableModel.clear()
        tableModel.rows = modelRows
    }
}
