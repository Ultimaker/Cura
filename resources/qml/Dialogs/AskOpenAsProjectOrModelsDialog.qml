// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1
import QtQuick.Window 2.1

import UM 1.3 as UM
import Cura 1.0 as Cura


UM.Dialog
{
    // This dialog asks the user whether he/she wants to open a project file as a project or import models.
    id: base

    title: catalog.i18nc("@title:window", "Open project file")
    width: UM.Theme.getSize("small_popup_dialog").width
    height: UM.Theme.getSize("small_popup_dialog").height

    maximumHeight: height
    maximumWidth: width
    minimumHeight: maximumHeight
    minimumWidth: maximumWidth

    modality: Qt.WindowModal

    property var fileUrl
    property var addToRecent: true //Whether to add this file to the recent files list after reading it.

    // load the entire project
    function loadProjectFile() {
        // update preference
        if (rememberChoiceCheckBox.checked) {
            UM.Preferences.setValue("cura/choice_on_open_project", "open_as_project")
        }

        UM.WorkspaceFileHandler.readLocalFile(base.fileUrl, base.addToRecent);

        base.hide()
    }

    // load the project file as separated models
    function loadModelFiles() {
        // update preference
        if (rememberChoiceCheckBox.checked) {
            UM.Preferences.setValue("cura/choice_on_open_project", "open_as_model")
        }

        CuraApplication.readLocalFile(base.fileUrl, "open_as_model", base.addToRecent)

        base.hide()
    }

    // override UM.Dialog accept
    function accept () {
        var openAsPreference = UM.Preferences.getValue("cura/choice_on_open_project")

        // when hitting 'enter', we always open as project unless open_as_model was explicitly stored as preference
        if (openAsPreference == "open_as_model") {
            loadModelFiles()
        } else {
            loadProjectFile()
        }
    }

    onVisibleChanged: {
        if (visible) {
            var rememberMyChoice = UM.Preferences.getValue("cura/choice_on_open_project") != "always_ask";
            rememberChoiceCheckBox.checked = rememberMyChoice;
        }
    }

    Column
    {
        anchors.fill: parent
        anchors.leftMargin: 20 * screenScaleFactor
        anchors.rightMargin: 20 * screenScaleFactor
        anchors.bottomMargin: 10 * screenScaleFactor
        spacing: 10 * screenScaleFactor

        Label
        {
            id: questionText
            text: catalog.i18nc("@text:window", "This is a Cura project file. Would you like to open it as a project or import the models from it?")
            anchors.left: parent.left
            anchors.right: parent.right
            font: UM.Theme.getFont("default")
            wrapMode: Text.WordWrap
        }

        CheckBox
        {
            id: rememberChoiceCheckBox
            text: catalog.i18nc("@text:window", "Remember my choice")
            checked: UM.Preferences.getValue("cura/choice_on_open_project") != "always_ask"
            style: CheckBoxStyle {
                label: Label {
                    text: control.text
                    font: UM.Theme.getFont("default")
                }
            }
        }

        // Buttons
        Item {
            id: buttonBar
            anchors.right: parent.right
            anchors.left: parent.left
            height: childrenRect.height

            Button {
                id: openAsProjectButton
                text: catalog.i18nc("@action:button", "Open as project")
                anchors.right: importModelsButton.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                isDefault: true
                onClicked: loadProjectFile()
            }

            Button {
                id: importModelsButton
                text: catalog.i18nc("@action:button", "Import models")
                anchors.right: parent.right
                onClicked: loadModelFiles()
            }
        }
    }
}
