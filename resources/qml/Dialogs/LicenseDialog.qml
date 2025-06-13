// Copyright (c) 2025 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.4
import QtQuick.Controls 2.9
import QtQuick.Layouts 1.3

import UM 1.6 as UM
import Cura 1.6 as Cura

UM.Dialog
{
    readonly property UM.I18nCatalog catalog: UM.I18nCatalog { name: "cura" }

    property var name
    property var version
    property var license

    id: base
    title: catalog.i18nc("@title:window The argument is a package name, and the second is the version.", "License for %1 %2").arg(name).arg(version)
    minimumWidth: 500 * screenScaleFactor

    Flickable
    {
        anchors.fill: parent
        contentHeight: labelLicense.height
        ScrollBar.vertical: UM.ScrollBar { }

        UM.Label
        {
            id: labelLicense
            width: parent.width
            text: license
        }
    }

    rightButtons: Cura.TertiaryButton
    {
        id: closeButton
        text: catalog.i18nc("@action:button", "Close")
        onClicked: reject()
    }
}
