// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.1

import UM 1.5 as UM
import Cura 1.0 as Cura


UM.Dialog
{
    // This dialog asks the user whether he/she wants to open a project file as a project or import models.
    id: base

    title: base.is_ucp
        ? catalog.i18nc("@title:window Don't translate 'Universal Cura Project'", "Open Universal Cura Project (UCP) file")
        : catalog.i18nc("@title:window", "Open project file")
    width: UM.Theme.getSize("small_popup_dialog").width
    height: UM.Theme.getSize("small_popup_dialog").height
    backgroundColor: UM.Theme.getColor("main_background")

    maximumHeight: height
    maximumWidth: width
    minimumHeight: maximumHeight
    minimumWidth: maximumWidth

    modality: Qt.ApplicationModal

    property var fileUrl
    property var addToRecent: true //Whether to add this file to the recent files list after reading it.
    property bool is_ucp: false

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
        spacing: UM.Theme.getSize("default_margin").height

        UM.Label
        {
            id: questionText
            width: parent.width
            text: base.is_ucp
                ? catalog.i18nc("@text:window", "This is a Cura Universal project file. Would you like to open it as a Cura project or Cura Universal Project or import the models from it?")
                : catalog.i18nc("@text:window", "This is a Cura project file. Would you like to open it as a project or import the models from it?")
            wrapMode: Text.WordWrap
        }

        UM.CheckBox
        {
            id: rememberChoiceCheckBox
            text: catalog.i18nc("@text:window", "Remember my choice")
            checked: UM.Preferences.getValue("cura/choice_on_open_project") != "always_ask"
        }
    }

    onAccepted: loadProjectFile()
    onRejected: loadModelFiles()

    buttonSpacing: UM.Theme.getSize("thin_margin").width

    rightButtons:
    [
        Cura.PrimaryButton
        {
            text: catalog.i18nc("@action:button", "Open as UCP")
            iconSource: UM.Theme.getIcon("CuraShareIcon")
            onClicked: loadProjectFile()
            visible: base.is_ucp
        },
        Cura.PrimaryButton
        {
            text: catalog.i18nc("@action:button", "Open as project")
            onClicked: loadProjectFile()
            visible: !base.is_ucp
        },
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@action:button", "Import models")
            onClicked: loadModelFiles()
        }
    ]
}
