// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM


//
// This component places a text on top of an image.
//
Column
{
    leftPadding: UM.Theme.getSize("default_margin").width
    rightPadding: UM.Theme.getSize("default_margin").width
    spacing: UM.Theme.getSize("default_margin").height
    property alias text: label.text
    property alias imageSource: image.source

    Label
    {
        id: label
        width: image.width
        anchors.horizontalCenter: image.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: ""
        wrapMode: Text.WordWrap
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        renderType: Text.NativeRendering
    }

    Image
    {
        id: image
        source: ""
    }
}