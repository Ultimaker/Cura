// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// Cura-style TextArea with scrolls
//
ScrollView
{
    property alias textArea: _textArea

    clip: true

    background: Rectangle  // Border
    {
        color: UM.Theme.getColor("main_background")
        border.color: UM.Theme.getColor("thick_lining")
        border.width: UM.Theme.getSize("default_lining").width
    }

    TextArea
    {
        id: _textArea
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        textFormat: TextEdit.PlainText
        renderType: Text.NativeRendering
        selectByMouse: true
    }
}
