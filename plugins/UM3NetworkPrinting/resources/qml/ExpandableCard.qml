// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM
import Cura 1.0 as Cura

/**
 * The expandable component has 3 major sub components:
 *  - The headerItem Always visible and should hold some info about what happens if the component is expanded
 *  - The popupItem The content that needs to be shown if the component is expanded.
 */
Item
{
    id: base

    property bool expanded: false
    property bool enabled: true
    property var borderWidth: 1
    property color borderColor: UM.Theme.getColor("monitor_card_border")
    property color headerBackgroundColor: UM.Theme.getColor("monitor_icon_accent")
    property color headerHoverColor: UM.Theme.getColor("monitor_card_hover")
    property color drawerBackgroundColor: UM.Theme.getColor("monitor_icon_accent")
    property alias headerItem: header.children
    property alias drawerItem: drawer.children

    width: parent.width
    height: childrenRect.height

    Rectangle
    {
        id: header
        border
        {
            color: borderColor
            width: borderWidth
        }
        color: base.enabled && headerMouseArea.containsMouse ? headerHoverColor : headerBackgroundColor
        height: childrenRect.height
        width: parent.width
        radius: 2 * screenScaleFactor // TODO: Theme!
        Behavior on color
        {
            ColorAnimation
            {
                duration: 100
            }
        }
    }

    MouseArea
    {
        id: headerMouseArea
        anchors.fill: header
        onClicked:
        {
            if (!base.enabled) return
            base.expanded = !base.expanded
        }
        hoverEnabled: base.enabled
    }

    Rectangle
    {
        id: drawer
        anchors
        {
            top: header.bottom
            topMargin: -1
        }
        border
        {
            color: borderColor
            width: borderWidth
        }
        clip: true
        color: headerBackgroundColor
        height: base.expanded ? childrenRect.height : 0
        width: parent.width
        radius: 2 * screenScaleFactor // TODO: Theme!
        Behavior on height
        {
            NumberAnimation
            {
                duration: 100
            }
        }
    }
}