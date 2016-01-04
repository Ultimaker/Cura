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
    minimumWidth: 400
    minimumHeight: 300;
    title: "Changelog"

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
        anchors.bottom:parent.bottom
        text: "close"
        onClicked: base.hide()
        anchors.horizontalCenter: parent.horizontalCenter
    }
}
