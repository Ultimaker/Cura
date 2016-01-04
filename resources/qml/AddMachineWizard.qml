// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM
import Cura 1.0 as Cura

import "WizardPages"

UM.Wizard
{
    id: base;

    title: catalog.i18nc("@title:window", "Add Printer")

    // This part is optional
    // This part checks whether there is a printer -> if not: some of the functions (delete for example) are disabled
    firstRun: false

    Component.onCompleted: {
        base.appendPage(Qt.resolvedUrl("WizardPages/AddMachine.qml"), catalog.i18nc("@title", "Add Printer"));
        base.currentPage = 0;
    }

    Item {
        UM.I18nCatalog { id: catalog; name: "cura"; }
    }
}
