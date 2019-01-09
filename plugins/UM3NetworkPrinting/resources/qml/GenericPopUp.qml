// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4
import QtQuick.Dialogs 1.1
import QtGraphicalEffects 1.0
import UM 1.3 as UM

/**
 * This is a generic pop-up element which can be supplied with a target and a content
 * item. The content item will appear to the left, right, above, or below the target
 * depending on the value of the direction property
 */
Popup
{
    id: base

    /**
     * The target item is what the pop-up is "tied" to, usually a button
     */
    property var target

    /**
     * Which side of the target should the contentItem appear on?
     * Possible values include:
     *   - "top"
     *   - "bottom"
     *   - "left"
     *   - "right"
     */
    property string direction: "bottom"

    /**
     * Should the popup close when you click outside it? For example, this is
     * disabled by the InfoBlurb component since it's opened and closed using mouse
     * hovers, not clicks.
     */
    property bool closeOnClick: true

    /**
     * Use white for context menus, dark grey for info blurbs!
     */
    property var color: "#ffffff" // TODO: Theme!

    background: Item
    {
        anchors.fill: parent

        DropShadow
        {
            anchors.fill: pointedRectangle
            color: UM.Theme.getColor("monitor_shadow")
            radius: UM.Theme.getSize("monitor_shadow_radius").width
            source: pointedRectangle
            transparentBorder: true
            verticalOffset: 2 * screenScaleFactor
        }

        Item
        {
            id: pointedRectangle
            anchors
            {
                horizontalCenter: parent.horizontalCenter
                verticalCenter: parent.verticalCenter
            }
            height: parent.height - 10 * screenScaleFactor // Because of the shadow
            width: parent.width - 10 * screenScaleFactor // Because of the shadow

            Rectangle
            {
                id: point
                anchors
                {
                    horizontalCenter:
                    {
                        switch(direction)
                        {
                            case "left":
                                return bloop.left
                            case "right":
                                return bloop.right
                            default:
                                return bloop.horizontalCenter
                        }
                    }
                    verticalCenter:
                    {
                        switch(direction)
                        {
                            case "top":
                                return bloop.top
                            case "bottom":
                                return bloop.bottom
                            default:
                                return bloop.verticalCenter
                        }
                    }
                }
                color: base.color
                height: 12 * screenScaleFactor
                transform: Rotation
                {
                    angle: 45
                    origin.x: point.width / 2
                    origin.y: point.height / 2
                }
                width: height
            }

            Rectangle
            {
                id: bloop
                anchors
                {
                    fill: parent
                    leftMargin:   direction == "left"   ? 8 * screenScaleFactor : 0
                    rightMargin:  direction == "right"  ? 8 * screenScaleFactor : 0
                    topMargin:    direction == "top"    ? 8 * screenScaleFactor : 0
                    bottomMargin: direction == "bottom" ? 8 * screenScaleFactor : 0
                }
                color: base.color
                width: parent.width
            }
        }
    }

    onClosed: visible = false
    onOpened: visible = true
    closePolicy: closeOnClick ? Popup.CloseOnPressOutside : Popup.NoAutoClose
    enter: Transition
    {
        NumberAnimation
        {
            duration: 75
            property: "visible"
        }
    }
    exit: Transition
    {
        NumberAnimation
        {
            duration: 75
            property: "visible"
        }
    }

    clip: true

    padding: UM.Theme.getSize("monitor_shadow_radius").width
    topPadding:    direction == "top"    ? padding + 8 * screenScaleFactor : padding
    bottomPadding: direction == "bottom" ? padding + 8 * screenScaleFactor : padding
    leftPadding:   direction == "left"   ? padding + 8 * screenScaleFactor : padding
    rightPadding:  direction == "right"  ? padding + 8 * screenScaleFactor : padding

    transformOrigin:
    {
        switch(direction)
        {
            case "top":
                return Popup.Top
            case "bottom":
                return Popup.Bottom
            case "right":
                return Popup.Right
            case "left":
                return Popup.Left
            default:
                direction = "bottom"
                return Popup.Bottom
        }
    }

    visible: false;

    x:
    {
        switch(direction)
        {
            case "left":
                return target.x + target.width + 4 * screenScaleFactor
            case "right":
                return target.x - base.width - 4 * screenScaleFactor
            default:
                return target.x + target.width / 2 - base.width / 2
        }
    }
    y:
    {
        switch(direction)
        {
            case "top":
                return target.y + target.height + 4 * screenScaleFactor
            case "bottom":
                return target.y - base.height - 4 * screenScaleFactor
            default:
                return target.y + target.height / 2 - base.height / 2
        }
    }
}
