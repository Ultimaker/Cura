// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.4 as UM
import Cura 1.1 as Cura

Row
{
    spacing: UM.Theme.getSize("default_margin").width

    Cura.ActionButton
    {
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Create account")
        color: UM.Theme.getColor("secondary")
        hoverColor: UM.Theme.getColor("secondary")
        textColor: UM.Theme.getColor("main_window_header_button_text_active")
        textHoverColor: UM.Theme.getColor("main_window_header_button_text_active")
        onClicked: Qt.openUrlExternally("https://account.ultimaker.com")
        fixedWidthMode: true
    }

    Cura.ActionButton
    {
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Login")
        onClicked: Cura.API.account.login()
        fixedWidthMode: true
    }
}