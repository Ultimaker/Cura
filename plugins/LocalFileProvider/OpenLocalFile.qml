// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Dialogs 1.2

import UM 1.3 as UM
import Cura 1.1 as Cura

Item
{
    id: base

    function show()
    {
        openDialog.visible = true;
    }

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    FileDialog
    {
        id: openDialog;

        //: File open dialog title
        title: catalog.i18nc("@title:window","Open file(s)")
        modality: Qt.WindowModal
        selectMultiple: true
        nameFilters: UM.MeshFileHandler.supportedReadFileTypes;
        folder:
        {
            //Because several implementations of the file dialog only update the folder when it is explicitly set.
            folder = CuraApplication.getDefaultPath("dialog_load_path");
            return CuraApplication.getDefaultPath("dialog_load_path");
        }
        onAccepted:
        {
            // Because several implementations of the file dialog only update the folder
            // when it is explicitly set.
            var f = folder;
            folder = f;

            CuraApplication.setDefaultPath("dialog_load_path", folder);

            handleOpenFileUrls(fileUrls);
        }

        // Yeah... I know... it is a mess to put all those things here.
        // There are lots of user interactions in this part of the logic, such as showing a warning dialog here and there,
        // etc. This means it will come back and forth from time to time between QML and Python. So, separating the logic
        // and view here may require more effort but make things more difficult to understand.
        function handleOpenFileUrls(fileUrlList)
        {
            // look for valid project files
            var projectFileUrlList = [];
            var hasGcode = false;
            var nonGcodeFileList = [];
            for (var i in fileUrlList)
            {
                var endsWithG = /\.g$/;
                var endsWithGcode = /\.gcode$/;
                if (endsWithG.test(fileUrlList[i]) || endsWithGcode.test(fileUrlList[i]))
                {
                    continue;
                }
                else if (CuraApplication.checkIsValidProjectFile(fileUrlList[i]))
                {
                    projectFileUrlList.push(fileUrlList[i]);
                }
                nonGcodeFileList.push(fileUrlList[i]);
            }
            hasGcode = nonGcodeFileList.length < fileUrlList.length;

            // show a warning if selected multiple files together with Gcode
            var hasProjectFile = projectFileUrlList.length > 0;
            var selectedMultipleFiles = fileUrlList.length > 1;
            if (selectedMultipleFiles && hasGcode)
            {
                infoMultipleFilesWithGcodeDialog.selectedMultipleFiles = selectedMultipleFiles;
                infoMultipleFilesWithGcodeDialog.hasProjectFile = hasProjectFile;
                infoMultipleFilesWithGcodeDialog.fileUrls = nonGcodeFileList.slice();
                infoMultipleFilesWithGcodeDialog.projectFileUrlList = projectFileUrlList.slice();
                infoMultipleFilesWithGcodeDialog.open();
            }
            else
            {
                handleOpenFiles(selectedMultipleFiles, hasProjectFile, fileUrlList, projectFileUrlList);
            }
        }

        function handleOpenFiles(selectedMultipleFiles, hasProjectFile, fileUrlList, projectFileUrlList)
        {
            // we only allow opening one project file
            if (selectedMultipleFiles && hasProjectFile)
            {
                openFilesIncludingProjectsDialog.fileUrls = fileUrlList.slice();
                openFilesIncludingProjectsDialog.show();
                return;
            }

            if (hasProjectFile)
            {
                var projectFile = projectFileUrlList[0];

                // check preference
                var choice = UM.Preferences.getValue("cura/choice_on_open_project");
                if (choice == "open_as_project")
                {
                    openFilesIncludingProjectsDialog.loadProjectFile(projectFile);
                }
                else if (choice == "open_as_model")
                {
                    openFilesIncludingProjectsDialog.loadModelFiles([projectFile].slice());
                }
                else    // always ask
                {
                    // ask whether to open as project or as models
                    askOpenAsProjectOrModelsDialog.fileUrl = projectFile;
                    askOpenAsProjectOrModelsDialog.show();
                }
            }
            else
            {
                openFilesIncludingProjectsDialog.loadModelFiles(fileUrlList.slice());
            }
        }
    }

    MessageDialog
    {
        id: infoMultipleFilesWithGcodeDialog
        title: catalog.i18nc("@title:window", "Open File(s)")
        icon: StandardIcon.Information
        standardButtons: StandardButton.Ok
        text: catalog.i18nc("@text:window", "We have found one or more G-Code files within the files you have selected. You can only open one G-Code file at a time. If you want to open a G-Code file, please just select only one.")

        property var selectedMultipleFiles
        property var hasProjectFile
        property var fileUrls
        property var projectFileUrlList

        onAccepted:
        {
            openDialog.handleOpenFiles(selectedMultipleFiles, hasProjectFile, fileUrls, projectFileUrlList);
        }
    }

    Cura.AskOpenAsProjectOrModelsDialog
    {
        id: askOpenAsProjectOrModelsDialog
    }

    Connections
    {
        target: CuraApplication
        onOpenProjectFile:
        {
            askOpenAsProjectOrModelsDialog.fileUrl = project_file;
            askOpenAsProjectOrModelsDialog.show();
        }
    }

    Cura.OpenFilesIncludingProjectsDialog
    {
        id: openFilesIncludingProjectsDialog
    }
}