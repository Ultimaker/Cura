// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Window 2.2

import UM 1.3 as UM
import Cura 1.1 as Cura


Window
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    title: catalog.i18nc("@title", "Welcome to Ultimaker Cura")
    modality: Qt.ApplicationModal
    flags: Qt.Window | Qt.FramelessWindowHint

    width: 580  // TODO
    height: 600  // TODO
    color: "transparent"

    StepPanel
    {
        id: stepPanel
        currentStep: 0
        model: CuraApplication.getWelcomePagesModel()
    }
}
