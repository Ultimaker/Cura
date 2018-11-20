// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.1 as UM

Button
{
    id: button
    property alias cursorShape: mouseArea.cursorShape
    property alias iconSource: buttonIcon.source
    property alias textFont: buttonText.font
    property alias cornerRadius: backgroundRect.radius
    property alias tooltip: tooltip.text
    property var color: UM.Theme.getColor("primary")
    property var hoverColor: UM.Theme.getColor("primary_hover")
    property var disabledColor: color
    property var textColor: UM.Theme.getColor("button_text")
    property var textHoverColor: UM.Theme.getColor("button_text_hover")
    property var textDisabledColor: textColor
    property var outlineColor: color
    property var outlineHoverColor: hoverColor
    property var outlineDisabledColor: outlineColor
    // This property is used to indicate whether the button has a fixed width or the width would depend on the contents
    // Be careful when using fixedWidthMode, the translated texts can be too long that they won't fit. In any case,
    // we elide the text to the right so the text will be cut off with the three dots at the end.
    property var fixedWidthMode: false

    leftPadding: UM.Theme.getSize("default_margin").width
    rightPadding: UM.Theme.getSize("default_margin").width
    height: UM.Theme.getSize("action_button").height

    contentItem: Row
    {
        UM.RecolorImage
        {
            id: buttonIcon
            source: ""
            height: Math.round(0.6 * parent.height)
            width: height
            sourceSize.width: width
            sourceSize.height: height
            color: button.hovered ? button.textHoverColor : button.textColor
            visible: source != ""
            anchors.verticalCenter: parent.verticalCenter
        }

        Label
        {
            id: buttonText
            text: button.text
            color: button.enabled ? (button.hovered ? button.textHoverColor : button.textColor): button.textDisabledColor
            font: UM.Theme.getFont("action_button")
            visible: text != ""
            renderType: Text.NativeRendering
            anchors.verticalCenter: parent.verticalCenter
            width: fixedWidthMode ? button.width - button.leftPadding - button.rightPadding : undefined
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
    }

    background: Rectangle
    {
        id: backgroundRect
        color: button.enabled ? (button.hovered ? button.hoverColor : button.color) : button.disabledColor
        radius: UM.Theme.getSize("action_button_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        border.color: button.enabled ? (button.hovered ? button.outlineHoverColor : button.outlineColor) : button.outlineDisabledColor
    }

    ToolTip
    {
        id: tooltip
        text: ""
        delay: 500
        visible: text != "" && button.hovered
    }

    MouseArea
    {
        id: mouseArea
        anchors.fill: parent
        onPressed: mouse.accepted = false
        hoverEnabled: true
    }
}
