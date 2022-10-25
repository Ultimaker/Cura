// Copyright (C) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.7 as Cura

Cura.TextField
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    leftPadding: searchIcon.width + UM.Theme.getSize("default_margin").width * 2

    placeholderText: catalog.i18nc("@placeholder", "Search")
    font: UM.Theme.getFont("default_italic")

    UM.ColorImage
    {
        id: searchIcon

        anchors
        {
            verticalCenter: parent.verticalCenter
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
        }
        source: UM.Theme.getIcon("Magnifier")
        height: UM.Theme.getSize("small_button_icon").height
        width: height
        color: UM.Theme.getColor("text")
    }
}
