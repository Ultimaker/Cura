// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.1

import UM 1.5 as UM
import Cura 1.5 as Cura

UM.Dialog
{
    // This dialog asks the user whether he/she wants to open the project file we have detected or the model files.
    id: base

    title: catalog.i18nc("@title:window", "Open file(s)")

    width: UM.Theme.getSize("small_popup_dialog").width
    height: UM.Theme.getSize("small_popup_dialog").height
    maximumHeight: height
    maximumWidth: width
    minimumHeight: height
    minimumWidth: width

    modality: Qt.ApplicationModal

    property var fileUrls: []
    property var addToRecent: true

    function loadProjectFile(projectFile)
    {
        UM.WorkspaceFileHandler.readLocalFile(projectFile, base.addToRecent);
    }

    function loadModelFiles(fileUrls)
    {
        for (var i in fileUrls)
        {
            CuraApplication.readLocalFile(fileUrls[i], "open_as_model", base.addToRecent);
        }
    }

    onAccepted: loadModelFiles(base.fileUrls)

    UM.Label
    {
        text: catalog.i18nc("@text:window", "We have found one or more project file(s) within the files you have selected. You can open only one project file at a time. We suggest to only import models from those files. Would you like to proceed?")
        anchors.left: parent.left
        anchors.right: parent.right
    }

    buttonSpacing: UM.Theme.getSize("thin_margin").width

    // Buttons
    rightButtons:
    [
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@action:button", "Cancel");
            onClicked: base.reject()
        },
        Cura.PrimaryButton
        {
            text: catalog.i18nc("@action:button", "Import all as models");
            onClicked: base.accept()
        }
    ]
}