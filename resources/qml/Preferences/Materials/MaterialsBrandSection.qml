// Copyright (c) 2018 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

Rectangle
{
    id: brand_section
    property var expanded: true
    property var types_model: model.material_types
    height: childrenRect.height
    width: parent.width
    Rectangle
    {
        id: brand_header_background
        color: UM.Theme.getColor("favorites_header_bar")
        anchors.fill: brand_header
    }
    Row
    {
        id: brand_header
        width: parent.width
        Label
        {
            id: brand_name
            text: model.name
            height: UM.Theme.getSize("favorites_row").height
            width: parent.width - UM.Theme.getSize("favorites_button").width
            verticalAlignment: Text.AlignVCenter
            leftPadding: 4
        }
        Button
        {
            text: ""
            implicitWidth: UM.Theme.getSize("favorites_button").width
            implicitHeight: UM.Theme.getSize("favorites_button").height
            UM.RecolorImage {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                    horizontalCenter: parent.horizontalCenter
                }
                width: UM.Theme.getSize("standard_arrow").width
                height: UM.Theme.getSize("standard_arrow").height
                sourceSize.width: width
                sourceSize.height: height
                color: "black"
                source: brand_section.expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
            }
            style: ButtonStyle
            {
                background: Rectangle
                {
                    anchors.fill: parent
                    color: "transparent"
                }
            }
        }
    }
    MouseArea
    {
        anchors.fill: brand_header
        onPressed:
        {
            brand_section.expanded = !brand_section.expanded
        }
    }
    Column
    {
        anchors.top: brand_header.bottom
        width: parent.width
        anchors.left: parent.left
        height: brand_section.expanded ? childrenRect.height : 0
        visible: brand_section.expanded
        Repeater
        {
            model: types_model
            delegate: MaterialsTypeSection {}
        }
    }
}