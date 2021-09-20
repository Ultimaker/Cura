// Copyright (c) 2021 Ultimaker B.V.
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
    property alias tooltipWidth: tooltip.width

    property color color: UM.Theme.getColor("primary")
    property color hoverColor: UM.Theme.getColor("primary_hover")
    property color disabledColor: color
    property color textColor: UM.Theme.getColor("button_text")
    property color textHoverColor: textColor
    property color textDisabledColor: disabledColor
    property color outlineColor: color
    property color outlineHoverColor: outlineColor
    property color outlineDisabledColor: disabledColor
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

    // These properties are deprecated.
    // To (maybe) prevent a major SDK upgrade, mark them as deprecated instead of just outright removing them.
    // Note, if you still want rounded corners, use (something based on) Cura.RoundedRectangle.
    property alias cornerSide: deprecatedProperties.cornerSide
    property alias shadowColor: deprecatedProperties.shadowColor
    property alias shadowEnabled: deprecatedProperties.shadowEnabled

    Item
    {
        id: deprecatedProperties

        visible: false
        enabled: false
        width: 0
        height: 0

        property var cornerSide: null
        property var shadowColor: null
        property var shadowEnabled: null

        onCornerSideChanged:
        {
            if (cornerSide != null)
            {
                CuraApplication.writeToLog("w", "'ActionButton.cornerSide' is deprecated since 4.11. Rounded corners can still be made with 'Cura.RoundedRectangle'.");
            }
        }
        onShadowColorChanged:
        {
            if (shadowColor != null)
            {
                CuraApplication.writeToLog("w", "'ActionButton.shadowColor' is deprecated since 4.11.")
            }
        }
        onShadowEnabledChanged:
        {
            if (shadowEnabled != null)
            {
                CuraApplication.writeToLog("w", "'ActionButton.shadowEnabled' is deprecated since 4.11.")
            }
        }
    }

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
                // When setting width directly, an unjust binding loop warning would be triggered,
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
        color: button.enabled ? (button.hovered ? button.hoverColor : button.color) : button.disabledColor
        border.width: UM.Theme.getSize("default_lining").width
        border.color: button.enabled ? (button.hovered ? button.outlineHoverColor : button.outlineColor) : button.outlineDisabledColor

        // Disable the rounded-ness of this rectangle. We can't use a normal Rectangle here yet, as the API/SDK has only just been deprecated.
        radius: 0
        cornerSide: Cura.RoundedRectangle.Direction.None
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
