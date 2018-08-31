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
    id: material_type_section
    property var expanded: base.collapsed_types.indexOf(model.brand + "_" + model.name) > -1
    property var colors_model: model.colors
    height: childrenRect.height
    width: parent.width
    Rectangle
    {
        id: material_type_header_background
        color: UM.Theme.getColor("lining")
        anchors.bottom: material_type_header.bottom
        anchors.left: material_type_header.left
        height: UM.Theme.getSize("default_lining").height
        width: material_type_header.width
    }
    Row
    {
        id: material_type_header
        width: parent.width - 8
        anchors
        {
            left: parent.left
            leftMargin: 8
        }
        Label
        {
            text: model.name
            height: UM.Theme.getSize("favorites_row").height
            width: parent.width - UM.Theme.getSize("favorites_button").width
            id: material_type_name
            verticalAlignment: Text.AlignVCenter
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
                source: material_type_section.expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
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
        anchors.fill: material_type_header
        onPressed:
        {
            const i = base.collapsed_types.indexOf(model.brand + "_" + model.name)
            if (i > -1)
            {
                // Remove it
                base.collapsed_types.splice(i, 1)
                material_type_section.expanded = false
            }
            else
            {
                // Add it
                base.collapsed_types.push(model.brand + "_" + model.name)
                material_type_section.expanded = true
            }
        }
    }
    Column
    {
        height: material_type_section.expanded ? childrenRect.height : 0
        visible: material_type_section.expanded
        width: parent.width
        anchors.top: material_type_header.bottom
        anchors.left: parent.left
        Repeater
        {
            model: colors_model
            delegate: MaterialsSlot {
                material: model
            }
        }
    }
}