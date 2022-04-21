//Copyright (C) 2022 Ultimaker B.V.
//Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Window 2.2
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.6 as Cura

import DigitalFactory 1.0 as DF

Window
{
    id: digitalFactoryOpenDialogBase
    title: "Open file from Library"

    modality: Qt.ApplicationModal
    width: 800 * screenScaleFactor
    height: 600 * screenScaleFactor
    minimumWidth: 800 * screenScaleFactor
    minimumHeight: 600 * screenScaleFactor

    Shortcut
    {
        sequence: "Esc"
        onActivated: digitalFactoryOpenDialogBase.close()
    }
    color: UM.Theme.getColor("main_background")

    SelectProjectPage
    {
        visible: manager.selectedProjectIndex == -1
        createNewProjectButtonVisible: false
    }

    OpenProjectFilesPage
    {
        visible: manager.selectedProjectIndex >= 0
        onOpenFilePressed: digitalFactoryOpenDialogBase.close()
    }


    BusyIndicator
    {
        // Shows up while Cura is waiting to receive the user's projects from the digital factory library
        id: retrievingProjectsBusyIndicator

        anchors {
            verticalCenter: parent.verticalCenter
            horizontalCenter: parent.horizontalCenter
        }

        width: parent.width / 4
        height: width
        visible: manager.retrievingProjectsStatus == DF.RetrievalStatus.InProgress
        running: visible
        palette.dark: UM.Theme.getColor("text")
    }
}
