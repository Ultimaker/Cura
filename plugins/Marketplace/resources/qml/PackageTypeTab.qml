// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import UM 1.0 as UM

TabButton
{
    property string pageTitle
    padding: UM.Theme.getSize("narrow_margin").width

    background: Rectangle
    {
        anchors.fill: parent
        color: parent.checked ? UM.Theme.getColor("main_background") : UM.Theme.getColor("detail_background")
        border.color: UM.Theme.getColor("detail_background")
        border.width: UM.Theme.getSize("thick_lining").width
    }

    contentItem: Label
    {
        text: parent.text
        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("text")
        width: contentWidth
        anchors.centerIn: parent
    }
}