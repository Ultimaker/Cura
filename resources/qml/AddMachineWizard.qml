// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

UM.Wizard{
    // This part checks whether there is a printer -> if not some of the functions (delete for example) are disabled
    // This part is optional
    property bool printer: true
    firstRun: printer ? false : true

    //: Add Printer dialog title
    wizardTitle: qsTr("Add Printer")

    wizardPages: [
        {
            title: "Add Printer",
            page: "AddMachine.qml"
        }
    ]
}
