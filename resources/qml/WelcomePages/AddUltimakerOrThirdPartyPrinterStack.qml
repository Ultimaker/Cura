// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.1 as Cura

ColumnLayout
{
    id: root

    UM.I18nCatalog { id: catalog; name: "cura" }

    Layout.fillWidth: true
    Layout.fillHeight: true

    property var goToUltimakerPrinter: () => layout.currentIndex = 1
    property var goToThirdPartyPrinter: () => layout.currentIndex = 2

    UM.Label
    {
        id: title_label
        Layout.fillWidth: true
        Layout.bottomMargin: UM.Theme.getSize("thick_margin").height
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Add printer")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
    }

    StackLayout
    {
        id: layout
        Layout.fillWidth: true
        Layout.fillHeight: true
        currentIndex: 0
        AddUltimakerOrThirdPartyPrinter
        {
            goToUltimakerPrinter: root.goToUltimakerPrinter
            goToThirdPartyPrinter: root.goToThirdPartyPrinter
        }
        AddUltimakerPrinter
        {
            goToThirdPartyPrinter: root.goToThirdPartyPrinter
        }
        AddThirdPartyPrinter
        {
            goToUltimakerPrinter: root.goToUltimakerPrinter

        }
    }
}