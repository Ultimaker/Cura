// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.4 as UM
import Cura 1.1 as Cura

Row
{
    spacing: UM.Theme.getSize("default_margin").width

    Cura.SecondaryButton
    {
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Create account")
        onClicked: Qt.openUrlExternally("https://account.ultimaker.com/app/create")
        fixedWidthMode: true
    }

    Cura.PrimaryButton
    {
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Login")
        onClicked: Cura.API.account.login()
        fixedWidthMode: true
    }
}