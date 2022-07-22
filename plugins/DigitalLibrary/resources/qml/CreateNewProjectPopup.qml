//Copyright (C) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Window 2.2
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.6 as Cura

import DigitalFactory 1.0 as DF


Popup
{
    id: base

    padding: UM.Theme.getSize("default_margin").width

    closePolicy: Popup.CloseOnEscape
    focus: true
    modal: true
    background: Cura.RoundedRectangle
    {
        cornerSide: Cura.RoundedRectangle.Direction.All
        border.color: UM.Theme.getColor("lining")
        border.width: UM.Theme.getSize("default_lining").width
        radius: UM.Theme.getSize("default_radius").width
        width: parent.width
        height: parent.height
        color: UM.Theme.getColor("main_background")
    }

    Connections
    {
        target: manager

        function onCreatingNewProjectStatusChanged(status)
        {
            if (status == DF.RetrievalStatus.Success)
            {
                base.close();
            }
        }
    }

    onOpened:
    {
        newProjectNameTextField.text = ""
        newProjectNameTextField.focus = true
    }

    Label
    {
        id: createNewLibraryProjectLabel
        text: "Create new Library project"
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("small_button_text")
        anchors
        {
            top: parent.top
            left: parent.left
            right: parent.right
        }
    }

    UM.Label
    {
        id: projectNameLabel
        text: "Project Name"
        anchors
        {
            top: createNewLibraryProjectLabel.bottom
            topMargin: UM.Theme.getSize("default_margin").width
            left: parent.left
            right: parent.right
        }
    }

    Cura.TextField
    {
        id: newProjectNameTextField
        width: parent.width
        anchors
        {
            top: projectNameLabel.bottom
            topMargin: UM.Theme.getSize("thin_margin").width
            left: parent.left
            right: parent.right
        }
        validator: RegularExpressionValidator
        {
            regularExpression: /^[^\\\/\*\?\|\[\]]{0,99}$/
        }

        text: PrintInformation.jobName
        font: UM.Theme.getFont("default")
        placeholderText: "Enter a name for your new project."
        onAccepted:
        {
            if (verifyProjectCreationButton.enabled)
            {
                verifyProjectCreationButton.clicked()
            }
        }
    }

    UM.Label
    {
        id: errorWhileCreatingProjectLabel
        text: manager.projectCreationErrorText
        width: parent.width
        wrapMode: Text.WordWrap
        color: UM.Theme.getColor("error")
        visible: manager.creatingNewProjectStatus == DF.RetrievalStatus.Failed
        anchors
        {
            top: newProjectNameTextField.bottom
            left: parent.left
            right: parent.right
        }
    }

    Cura.SecondaryButton
    {
        id: cancelProjectCreationButton

        anchors.bottom: parent.bottom
        anchors.left: parent.left

        text: "Cancel"

        onClicked:
        {
            base.close()
        }
        busy: false
    }

    Cura.PrimaryButton
    {
        id: verifyProjectCreationButton

        anchors.bottom: parent.bottom
        anchors.right: parent.right
        text: "Create"
        enabled: newProjectNameTextField.text.length >= 2 && !busy

        onClicked:
        {
            manager.createLibraryProjectAndSetAsPreselected(newProjectNameTextField.text)
        }
        busy: manager.creatingNewProjectStatus == DF.RetrievalStatus.InProgress
    }
}
