// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 2.10

import UM 1.5 as UM
import Cura 1.7 as Cura


Item
{
    property Component content: Item { visible: false  }
    property alias settingName: settingLabel.text

    UM.Label
    {
        id: settingLabel
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        text: "TEST"
    }


    Loader
    {
        id: settingLoader
        width: parent.width
        height: content.height
        anchors.left: settingLabel.right
        anchors.right: parent.right
        anchers.verticalCenter: parent.verticalCenter
        sourceComponent: content
    }
}