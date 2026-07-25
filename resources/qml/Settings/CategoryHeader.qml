// Copyright (c) 2026 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

// Non-collapsible category header used in the tabbed settings view.

import QtQuick
import QtQuick.Controls

import UM 1.5 as UM

Rectangle
{
    id: base

    height: UM.Theme.getSize("section_header").height
    color: UM.Theme.getColor("setting_category")

    property bool expanded: true
    property alias categoryIcon: icon.source
    property alias labelText: categoryLabel.text
    property alias labelFont: categoryLabel.font

    signal showTooltip(string text)
    signal hideTooltip()
    signal contextMenuRequested()
    signal showAllHiddenInheritedSettings(string category_id)
    signal focusReceived()
    signal setActiveFocusToNextSetting(bool forward)

    Item
    {
        id: content
        anchors.fill: parent
        anchors.leftMargin: UM.Theme.getSize("narrow_margin").width

        UM.ColorImage
        {
            id: icon
            source: ""
            visible: source != ""
            anchors.verticalCenter: parent.verticalCenter
            color: UM.Theme.getColor("setting_category_text")
            width: visible ? UM.Theme.getSize("section_icon").width : 0
            height: UM.Theme.getSize("section_icon").height
        }

        UM.Label
        {
            id: categoryLabel
            anchors.right: parent.right
            anchors.left: icon.right
            anchors.leftMargin: UM.Theme.getSize("narrow_margin").width
            anchors.verticalCenter: parent.verticalCenter
            elide: Text.ElideRight
            wrapMode: Text.NoWrap
            font: UM.Theme.getFont("medium_bold")
            color: UM.Theme.getColor("setting_category_text")
        }
    }
}
