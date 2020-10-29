// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtGraphicalEffects 1.0 // For the dropshadow

import UM 1.1 as UM
import Cura 1.0 as Cura


Button
{
    id: button
    property bool isIconOnRightSide: false

    property alias iconSource: buttonIconLeft.source
    property alias textFont: buttonText.font
    property alias cornerRadius: backgroundRect.radius
    property alias tooltip: tooltip.tooltipText
    property alias cornerSide: backgroundRect.cornerSide

    property color color: UM.Theme.getColor("primary")
    property color hoverColor: UM.Theme.getColor("primary_hover")
    property color disabledColor: color
    property color textColor: UM.Theme.getColor("button_text")
    property color textHoverColor: textColor
    property color textDisabledColor: textColor
    property color outlineColor: color
    property color outlineHoverColor: hoverColor
    property color outlineDisabledColor: outlineColor
    property alias shadowColor: shadow.color
    property alias shadowEnabled: shadow.visible
    property alias busy: busyIndicator.visible

    property bool underlineTextOnHover: false

    property alias toolTipContentAlignment: tooltip.contentAlignment

    // This property is used to indicate whether the button has a fixed width or the width would depend on the contents
    // Be careful when using fixedWidthMode, the translated texts can be too long that they won't fit. In any case,
    // we elide the text to the right so the text will be cut off with the three dots at the end.
    property var fixedWidthMode: false

    // This property is used when the space for the button is limited. In case the button needs to grow with the text,
    // but it can exceed a maximum, then this value have to be set.
    property int maximumWidth: 0

    leftPadding: UM.Theme.getSize("default_margin").width
    rightPadding: UM.Theme.getSize("default_margin").width
    height: UM.Theme.getSize("action_button").height
    hoverEnabled: true

    onHoveredChanged:
    {
        if(underlineTextOnHover)
        {
            buttonText.font.underline = hovered
        }
    }

    contentItem: Row
    {
        spacing: UM.Theme.getSize("narrow_margin").width
        height: button.height
        //Left side icon. Only displayed if !isIconOnRightSide.
        UM.RecolorImage
        {
            id: buttonIconLeft
            source: ""
            height: visible ? UM.Theme.getSize("action_button_icon").height : 0
            width: visible ? height : 0
            sourceSize.width: width
            sourceSize.height: height
            color: button.enabled ? (button.hovered ? button.textHoverColor : button.textColor) : button.textDisabledColor
            visible: source != "" && !button.isIconOnRightSide
            anchors.verticalCenter: parent.verticalCenter
        }

        TextMetrics
        {
            id: buttonTextMetrics
            text: buttonText.text
            font: buttonText.font
            elide: buttonText.elide
            elideWidth: buttonText.width
        }

        Label
        {
            id: buttonText
            text: button.text
            color: button.enabled ? (button.hovered ? button.textHoverColor : button.textColor): button.textDisabledColor
            font: UM.Theme.getFont("medium")
            visible: text != ""
            renderType: Text.NativeRendering
            height: parent.height
            anchors.verticalCenter: parent.verticalCenter
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight

            Binding
            {
                // When settting width directly, an unjust binding loop warning would be triggered,
                // because button.width is part of this expression.
                // Using parent.width is fine in fixedWidthMode.
                target: buttonText
                property: "width"
                value: button.fixedWidthMode ? button.width - button.leftPadding - button.rightPadding
                                             : ((maximumWidth != 0 && button.contentWidth > maximumWidth) ? maximumWidth : undefined)
            }
        }

        //Right side icon. Only displayed if isIconOnRightSide.
        UM.RecolorImage
        {
            id: buttonIconRight
            source: buttonIconLeft.source
            height: visible ? UM.Theme.getSize("action_button_icon").height : 0
            width: visible ? height : 0
            sourceSize.width: width
            sourceSize.height: height
            color: buttonIconLeft.color
            visible: source != "" && button.isIconOnRightSide
            anchors.verticalCenter: buttonIconLeft.verticalCenter
        }
    }

    background: Cura.RoundedRectangle
    {
        id: backgroundRect
        cornerSide: Cura.RoundedRectangle.Direction.All
        color: button.enabled ? (button.hovered ? button.hoverColor : button.color) : button.disabledColor
        radius: UM.Theme.getSize("action_button_radius").width
        border.width: UM.Theme.getSize("default_lining").width
        border.color: button.enabled ? (button.hovered ? button.outlineHoverColor : button.outlineColor) : button.outlineDisabledColor
    }

    DropShadow
    {
        id: shadow
        // Don't blur the shadow
        radius: 0
        anchors.fill: backgroundRect
        source: backgroundRect
        verticalOffset: 2
        visible: false
        // Should always be drawn behind the background.
        z: backgroundRect.z - 1
    }

    Cura.ToolTip
    {
        id: tooltip
        visible:
        {
            if (!button.hovered)
            {
                return false;
            }
            if (tooltipText == button.text)
            {
                return buttonTextMetrics.elidedText != buttonText.text;
            }
            return true;
        }
        targetPoint: Qt.point(parent.x, Math.round(parent.y + parent.height / 2))
    }

    BusyIndicator
    {
        id: busyIndicator

        anchors.centerIn: parent

        width: height
        height: parent.height

        visible: false

        RotationAnimator
        {
            target: busyIndicator.contentItem
            running: busyIndicator.visible && busyIndicator.running
            from: 0
            to: 360
            loops: Animation.Infinite
            duration: 2500
        }
    }
}