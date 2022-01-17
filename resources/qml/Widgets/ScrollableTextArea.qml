// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// Cura-style TextArea with scrolls
//
ScrollView
{
    id: scrollableTextAreaBase
    property alias textArea: _textArea

    property var back_color: UM.Theme.getColor("main_background")
    property var do_borders: true

    clip: true
    ScrollBar.vertical: UM.ScrollBar
    {
        parent: scrollableTextAreaBase
        anchors
        {
            right: parent.right
            rightMargin: parent.background.border.width
            top: parent.top
            topMargin: anchors.rightMargin
            bottom: parent.bottom
            bottomMargin: anchors.rightMargin
        }
    }

    background: Rectangle  // Border
    {
        color: back_color
        border.color: UM.Theme.getColor("thick_lining")
        border.width: do_borders ? UM.Theme.getSize("default_lining").width : 0
    }

    TextArea
    {
        id: _textArea
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        textFormat: TextEdit.PlainText
        renderType: Text.NativeRendering
        wrapMode: Text.Wrap
        selectByMouse: true
    }
}
