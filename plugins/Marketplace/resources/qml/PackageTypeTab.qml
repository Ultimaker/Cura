// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import UM 1.5 as UM

TabButton
{
    property string pageTitle
    padding: UM.Theme.getSize("narrow_margin").width
    horizontalPadding: UM.Theme.getSize("default_margin").width
    hoverEnabled: true
    property color inactiveBackgroundColor : hovered ? UM.Theme.getColor("action_button_hovered") : UM.Theme.getColor("detail_background")
    property color activeBackgroundColor : UM.Theme.getColor("main_background")

    background: Rectangle
    {
        anchors.fill: parent
        color: parent.checked ? activeBackgroundColor : inactiveBackgroundColor
        border.color: UM.Theme.getColor("detail_background")
        border.width: UM.Theme.getSize("thick_lining").width
    }

    contentItem: UM.Label
    {
        text: parent.text
        font: UM.Theme.getFont("medium_bold")
        width: contentWidth
        anchors.centerIn: parent
    }
}