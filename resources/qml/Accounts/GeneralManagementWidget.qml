// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.4 as UM
import Cura 1.1 as Cura

import "../components"

Column
{
    ActionButton
    {
        text: catalog.i18nc("@button", "Sign In")
        color: "transparent"
        hoverColor: "transparent"
        textColor: UM.Theme.getColor("text")
        textHoverColor: UM.Theme.getColor("text_link")
        onClicked: Cura.API.account.login()
    }
}