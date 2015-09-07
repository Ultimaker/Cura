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
    width: 300 * Screen.devicePixelRatio;
    height: 500 * Screen.devicePixelRatio;
    title: "Changelog"
    ScrollView
    {
        anchors.fill:parent
        Text
        {
            text: manager.getChangeLogString()
            width:base.width - 35
            wrapMode: Text.Wrap;
            //Component.onCompleted: console.log()
        }
    }
}
