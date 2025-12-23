// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the "Add a printer" (network) page of the welcome on-boarding process.
//
Control
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    property var goToUltimakerPrinter
    property var goToThirdPartyPrinter

    contentItem: ColumnLayout
    {
        Layout.fillWidth: true
        Layout.fillHeight: true

        UM.Label
        {
            text: catalog.i18nc("@label", "In order to start using Cura you will need to configure a printer.")
            font: UM.Theme.getFont("default")
            Layout.alignment: Qt.AlignTop
        }

        UM.Label
        {
            text: catalog.i18nc("@label", "What printer would you like to setup?")
            font: UM.Theme.getFont("default_bold")
            Layout.alignment: Qt.AlignTop
        }

        RowLayout
        {
            spacing: UM.Theme.getSize("wide_margin").width
            Layout.preferredWidth: childrenRect.width
            Layout.preferredHeight: childrenRect.height
            Layout.topMargin: UM.Theme.getSize("wide_margin").height
            Layout.bottomMargin: UM.Theme.getSize("wide_margin").height
            Layout.alignment: Qt.AlignTop | Qt.AlignHCenter

            PrinterCard
            {
                id: ultimakerPrinterCard
                Layout.alignment: Qt.AlignBottom
                onClicked: goToUltimakerPrinter
                text: catalog.i18nc("@button", "UltiMaker printer")
                imageSource: UM.Theme.getImage("ultimaker_printer")
            }

            PrinterCard
            {
                id: thrirdPartyPrinterCard
                Layout.alignment: Qt.AlignBottom
                onClicked: goToThirdPartyPrinter
                text: catalog.i18nc("@button", "Non UltiMaker printer")
                imageSource: UM.Theme.getImage("third_party_printer")
            }
        }
    }
}