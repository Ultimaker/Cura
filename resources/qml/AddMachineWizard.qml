// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM
import Cura 1.0 as Cura

UM.Wizard
{
    //: Add Printer dialog title
    wizardTitle: qsTr("Add Printer")
    wizardPages: [
        {
            title: "Add Printer",
            page: UM.Resources.getPath(Cura.ResourceTypes.QmlFiles, "WizardPages/AddMachine.qml")
        }
    ]

    // This part is optional
    // This part checks whether there is a printer -> if not: some of the functions (delete for example) are disabled
    property bool printer: true
    firstRun: printer ? false : true
}
