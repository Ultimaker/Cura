// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the first page of the welcome on-boarding process.
//
Column
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    spacing: 60

    // Placeholder
    Label { text: " " }

    Label
    {
        id: titleLabel
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Welcome to Ultimaker Cura")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("large_bold")
        renderType: Text.NativeRendering
    }

    Column
    {
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 40

        Image
        {
            id: curaImage
            anchors.horizontalCenter: parent.horizontalCenter
            source: UM.Theme.getImage("first_run_welcome_cura")
        }

        Label
        {
            id: textLabel
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            text: catalog.i18nc("@text", "Please follow these steps to set up\nUltimaker Cura. This will only take a few moments.")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
        }
    }

    Cura.PrimaryButton
    {
        id: getStartedButton
        anchors.horizontalCenter: parent.horizontalCenter
        text: catalog.i18nc("@button", "Get started")
        width: 140
        fixedWidthMode: true
    }
}
