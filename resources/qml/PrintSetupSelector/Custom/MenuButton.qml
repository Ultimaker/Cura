// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.5 as UM
import Cura 1.6 as Cura

Button
{
    // This is a work around for a qml issue. Since the default button uses a private implementation for contentItem
    // (the so called IconText), which handles the mnemonic conversion (aka; ensuring that &Button) text property
    // is rendered with the B underlined. Since we're also forced to mix controls 1.0 and 2.0 actions together,
    // we need a special property for the text of the label if we do want it to be rendered correctly, but don't want
    // another shortcut to be added (which will cause for "QQuickAction::event: Ambiguous shortcut overload: " to
    // happen.
    property string labelText: ""
    id: button
    hoverEnabled: true
    leftPadding:UM.Theme.getSize("wide_margin").width

    background: Rectangle
    {
        id: backgroundRectangle
        color: button.hovered ? UM.Theme.getColor("background_2"): UM.Theme.getColor("background_1")
    }

    // Workaround to ensure that the mnemonic highlighting happens correctly
    function replaceText(txt)
    {
        var index = txt.indexOf("&")
        if(index >= 0)
        {
            txt = txt.replace(txt.substr(index, 2), ("<u>" + txt.substr(index + 1, 1) + "</u>"))
        }
        return txt
    }

    contentItem: UM.Label
    {
        id: textLabel
        text: button.text != "" ? replaceText(button.text) : replaceText(button.labelText)
        height: contentHeight
        color: button.enabled ? UM.Theme.getColor("text") :UM.Theme.getColor("text_inactive")
    }
}