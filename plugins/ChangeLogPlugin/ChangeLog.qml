// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    id: base
    minimumWidth: 400 * Screen.devicePixelRatio
    minimumHeight: 300 * Screen.devicePixelRatio
    width: minimumWidth
    height: minimumHeight
    title: catalog.i18nc("@label", "Changelog")

    ScrollView
    {
        width: parent.width
        height: parent.height - 25
        Text
        {
            text: manager.getChangeLogString()
            width:base.width - 35
            wrapMode: Text.Wrap;
        }
    }
    Button
    {
        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }
        anchors.bottom:parent.bottom
        text: catalog.i18nc("@action:button", "Close")
        onClicked: base.hide()
        anchors.horizontalCenter: parent.horizontalCenter
    }
}
