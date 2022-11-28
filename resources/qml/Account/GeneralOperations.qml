// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura

Column
{
    spacing: UM.Theme.getSize("default_margin").width
    padding: UM.Theme.getSize("default_margin").width

    UM.Label
    {
        id: title
        anchors.horizontalCenter: parent.horizontalCenter
        text: catalog.i18nc("@label", "Sign in to the UltiMaker platform")
        font: UM.Theme.getFont("large_bold")
    }

    Image
    {
        id: machinesImage
        anchors.horizontalCenter: parent.horizontalCenter
        source: UM.Theme.getImage("welcome_cura")
        width: parent.width / 2
        fillMode: Image.PreserveAspectFit
        horizontalAlignment: Image.AlignHCenter
        verticalAlignment: Image.AlignVCenter
    }

    UM.Label
    {
        id: generalInformationPoints
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignLeft
        text: catalog.i18nc("@text", "- Add material profiles and plug-ins from the Marketplace\n- Back-up and sync your material profiles and plug-ins\n- Share ideas and get help from 48,000+ users in the UltiMaker community")
        lineHeight: 1.4
        wrapMode: Text.NoWrap
    }

    Cura.PrimaryButton
    {
        anchors.horizontalCenter: parent.horizontalCenter
        width: UM.Theme.getSize("account_button").width
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Sign in")
        onClicked: Cura.API.account.login()
        fixedWidthMode: true
    }

    Cura.TertiaryButton
    {
        anchors.horizontalCenter: parent.horizontalCenter
        height: UM.Theme.getSize("account_button").height
        text: catalog.i18nc("@button", "Create a free UltiMaker account")
        onClicked: Qt.openUrlExternally("https://ultimaker.com/app/ultimaker-cura-account-sign-up?utm_source=cura&utm_medium=software&utm_campaign=menu-signup")
    }
}
