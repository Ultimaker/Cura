// Copyright (c) 2022 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

// Button used to collapse and de-collapse group, or a category, of settings
// the button contains
//   - the title of the category,
//   - an optional icon and
//   - a chevron button to display the colapsetivity of the settings
// Mainly used for the collapsable categories in the settings pannel

import QtQuick 2.2
import QtQuick.Controls 2.1

import UM 1.5 as UM

Button
{
    id: base

    height: enabled ? UM.Theme.getSize("section_header").height : 0

    property var expanded: false

    property alias arrow: categoryArrow
    property alias categoryIcon: icon.source
    property alias labelText: categoryLabel.text

    states:
    [
        State
        {
            name: "disabled"
            when: !base.enabled
            PropertyChanges { target: categoryLabel; color: UM.Theme.getColor("setting_category_disabled_text") }
            PropertyChanges { target: icon; color: UM.Theme.getColor("setting_category_disabled_text") }
            PropertyChanges { target: backgroundRectangle; color: UM.Theme.getColor("setting_category_disabled") }
        },
        State
        {
            name: "hovered"
            when: base.hovered
            PropertyChanges { target: categoryLabel; color: UM.Theme.getColor("setting_category_active_text") }
            PropertyChanges { target: icon; color: UM.Theme.getColor("setting_category_active_text") }
            PropertyChanges { target: backgroundRectangle; color: UM.Theme.getColor("setting_category_hover") }
        },
        State
        {
            name: "active"
            when: base.pressed || base.activeFocus
            PropertyChanges { target: categoryLabel; color: UM.Theme.getColor("setting_category_active_text") }
            PropertyChanges { target: icon; color: UM.Theme.getColor("setting_category_active_text") }
            PropertyChanges { target: backgroundRectangle; color: UM.Theme.getColor("setting_category") }
        }
    ]

    background: Rectangle
    {
        id: backgroundRectangle
        height: base.height

        color: UM.Theme.getColor("setting_category")
        Behavior on color { ColorAnimation { duration: 50 } }

        Rectangle
        {
            //Lining on top
            anchors.top: parent.top
            color: UM.Theme.getColor("border_main")
            height: UM.Theme.getSize("default_lining").height
            width: parent.width
        }
    }

    contentItem: Item
    {
        anchors.fill: parent

        UM.Label
        {
            id: categoryLabel
            anchors
            {
                left: parent.left
                leftMargin: UM.Theme.getSize("default_margin").width + UM.Theme.getSize("section_icon").width
                right: parent.right
                verticalCenter: parent.verticalCenter
            }
            textFormat: Text.PlainText
            font: UM.Theme.getFont("medium_bold")
            color: UM.Theme.getColor("setting_category_text")
            fontSizeMode: Text.HorizontalFit
            minimumPointSize: 8
        }

        UM.RecolorImage
        {
            id: categoryArrow
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: UM.Theme.getSize("narrow_margin").width
            width: UM.Theme.getSize("standard_arrow").width
            height: UM.Theme.getSize("standard_arrow").height
            sourceSize.height: width
            color: UM.Theme.getColor("setting_control_button")
            source: expanded ? UM.Theme.getIcon("ChevronSingleDown") : UM.Theme.getIcon("ChevronSingleLeft")
        }
    }

    UM.RecolorImage
    {
        id: icon
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("narrow_margin").width
        color: UM.Theme.getColor("setting_category_text")
        width: UM.Theme.getSize("section_icon").width
        height: UM.Theme.getSize("section_icon").height
        sourceSize.width: width
        sourceSize.height: width
    }
}