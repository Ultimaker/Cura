// Copyright (c) 2017 Ultimaker B.V.
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
    // This dialog asks the user whether he/she wants to open the project file we have detected or the model files.
    id: base

    title: catalog.i18nc("@title:window", "Open file(s)")
    width: 420 * screenScaleFactor
    height: 170 * screenScaleFactor

    maximumHeight: height
    maximumWidth: width
    minimumHeight: height
    minimumWidth: width

    modality: Qt.WindowModal

    property var fileUrls: []
    property int spacerHeight: 10 * screenScaleFactor

    function loadProjectFile(projectFile)
    {
        UM.WorkspaceFileHandler.readLocalFile(projectFile);

        var meshName = backgroundItem.getMeshName(projectFile.toString());
        backgroundItem.hasMesh(decodeURIComponent(meshName));
    }

    function loadModelFiles(fileUrls)
    {
        for (var i in fileUrls)
        {
            CuraApplication.readLocalFile(fileUrls[i], "open_as_model");
        }

        var meshName = backgroundItem.getMeshName(fileUrls[0].toString());
        backgroundItem.hasMesh(decodeURIComponent(meshName));
    }

    Column
    {
        anchors.fill: parent
        anchors.leftMargin: 20 * screenScaleFactor
        anchors.rightMargin: 20 * screenScaleFactor
        anchors.bottomMargin: 20 * screenScaleFactor
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 10 * screenScaleFactor

        Label
        {
            text: catalog.i18nc("@text:window", "We have found one or more project file(s) within the files you have selected. You can open only one project file at a time. We suggest to only import models from those files. Would you like to proceed?")
            anchors.left: parent.left
            anchors.right: parent.right
            font: UM.Theme.getFont("default")
            wrapMode: Text.WordWrap
        }

        Item // Spacer
        {
            height: base.spacerHeight
            width: height
        }

        // Buttons
        Item
        {
            anchors.right: parent.right
            anchors.left: parent.left
            height: childrenRect.height

            Button
            {
                id: cancelButton
                text: catalog.i18nc("@action:button", "Cancel");
                anchors.right: importAllAsModelsButton.left
                onClicked:
                {
                    // cancel
                    base.hide();
                }
            }

            Button
            {
                id: importAllAsModelsButton
                text: catalog.i18nc("@action:button", "Import all as models");
                anchors.right: parent.right
                isDefault: true
                onClicked:
                {
                    // load models from all selected file
                    loadModelFiles(base.fileUrls);

                    base.hide();
                }
            }
        }
    }
}
