// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

import ".."


//
// This is DropDown Header bar of the expandable drop down list. See comments in DropDownWidget for details.
//
Cura.RoundedRectangle
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    id: base

    border.width: UM.Theme.getSize("default_lining").width
    border.color: UM.Theme.getColor("lining")
    color: UM.Theme.getColor("secondary")
    radius: UM.Theme.getSize("default_radius").width

    cornerSide: contentShown ? Cura.RoundedRectangle.Direction.Up : Cura.RoundedRectangle.Direction.All

    property string title: ""
    property url rightIconSource: UM.Theme.getIcon("ChevronSingleDown")

    // If the tab is under hovering state
    property bool hovered: false
    // If the content is shown
    property bool contentShown: false

    signal clicked()

    MouseArea
    {
        anchors.fill: parent
        hoverEnabled: true
        onEntered: base.hovered = true
        onExited: base.hovered = false

        onClicked: base.clicked()
    }

    Label
    {
        id: title
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.verticalCenter: parent.verticalCenter
        verticalAlignment: Text.AlignVCenter
        text: base.title
        font: UM.Theme.getFont("medium")
        renderType: Text.NativeRendering
        color: base.hovered ? UM.Theme.getColor("small_button_text_hover") : UM.Theme.getColor("small_button_text")
    }

    UM.RecolorImage
    {
        id: rightIcon
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        anchors.verticalCenter: parent.verticalCenter
        width: UM.Theme.getSize("message_close").width
        height: UM.Theme.getSize("message_close").height
        color: base.hovered ? UM.Theme.getColor("small_button_text_hover") : UM.Theme.getColor("small_button_text")
        source: base.rightIconSource
    }
}
