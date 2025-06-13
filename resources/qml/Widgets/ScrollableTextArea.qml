// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// Cura-style TextArea with scrolls
//
Flickable
{
    id: scrollableTextAreaBase
    property bool do_borders: true
    property var back_color: UM.Theme.getColor("main_background")
    property alias textArea: flickableTextArea

    ScrollBar.vertical: UM.ScrollBar {}

    TextArea.flickable: TextArea
    {
        id: flickableTextArea

        background: Rectangle //Providing the background color and border.
        {
            anchors.fill: parent
            anchors.margins: -border.width

            color: scrollableTextAreaBase.back_color
            border.color: UM.Theme.getColor("thick_lining")
            border.width: scrollableTextAreaBase.do_borders ? UM.Theme.getSize("default_lining").width : 0
        }

        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        textFormat: TextEdit.PlainText
        renderType: Text.NativeRendering
        wrapMode: Text.Wrap
        selectByMouse: true
    }
}