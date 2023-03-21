// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.0 as Cura

// Reusable component that holds an (re-colorable) icon on the left with some text on the right.
// This component is also designed to be used with layouts. It will use the width of the text + icon as preferred width
// It sets the icon size + half of the content as its minimum width (in which case it will elide the text)
Item
{
    property alias source: icon.source
    property alias iconSize: icon.width
    property alias iconColor: icon.color
    property alias color: label.color
    property alias text: label.text
    property alias font: label.font
    property alias elide: label.elide
    property real margin: UM.Theme.getSize("narrow_margin").width
    property alias wrapMode: label.wrapMode
    property real spacing: UM.Theme.getSize("narrow_margin").width

    property string tooltipText: ""

    // These properties can be used in combination with layouts.
    readonly property real contentWidth: icon.width + margin + label.contentWidth
    readonly property real minContentWidth: Math.round(icon.width + margin + 0.5 * label.contentWidth)

    Layout.minimumWidth: minContentWidth
    Layout.preferredWidth: contentWidth
    Layout.fillHeight: true
    Layout.fillWidth: true

    implicitWidth: icon.width + 100
    implicitHeight: icon.height

    UM.ColorImage
    {
        id: icon
        width: UM.Theme.getSize("section_icon").width
        height: width

        color: UM.Theme.getColor("icon")

        anchors
        {
            left: parent.left
            verticalCenter: parent.verticalCenter
        }
    }

    UM.Label
    {
        id: label
        elide: Text.ElideRight
        anchors
        {
            left: icon.right
            right: parent.right
            top: parent.top
            bottom: parent.bottom
            rightMargin: 0
            leftMargin: spacing
            margins: margin
        }
    }

    MouseArea
    {
        enabled: tooltipText != ""
        anchors.fill: parent
        hoverEnabled: true
        onEntered: base.showTooltip(parent, Qt.point(-UM.Theme.getSize("thick_margin").width, 0), tooltipText)
        onExited: base.hideTooltip()
    }
}