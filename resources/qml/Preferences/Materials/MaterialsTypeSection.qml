// Copyright (c) 2018 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: material_type_section
    property var materialType

    property string materialBrand: materialType != null ? materialType.brand : ""
    property string materialName: materialType != null ? materialType.name : ""
    property var expanded: materialList.expandedTypes.indexOf(materialBrand + "_" + materialName) > -1
    property var colorsModel: materialType != null ? materialType.colors: null
    height: childrenRect.height
    width: parent.width
    anchors.left: parent.left
    Rectangle
    {
        id: material_type_header_background
        color:
        {
            if(!expanded && materialBrand + "_" + materialName == materialList.currentType)
            {
                return UM.Theme.getColor("favorites_row_selected")
            }
            else
            {
                return "transparent"
            }
        }
        width: parent.width
        height: material_type_header.height
    }
    Rectangle
    {
        id: material_type_header_border
        color: UM.Theme.getColor("favorites_header_bar")
        anchors.bottom: material_type_header.bottom
        anchors.left: material_type_header.left
        height: UM.Theme.getSize("default_lining").height
        width: material_type_header.width
    }
    Row
    {
        id: material_type_header
        width: parent.width
        leftPadding: UM.Theme.getSize("default_margin").width
        anchors
        {
            left: parent.left
        }
        Label
        {
            text: materialName
            height: UM.Theme.getSize("favorites_row").height
            width: parent.width - parent.leftPadding - UM.Theme.getSize("favorites_button").width
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
            const identifier = materialBrand + "_" + materialName;
            const i = materialList.expandedTypes.indexOf(identifier)
            if (i > -1)
            {
                // Remove it
                materialList.expandedTypes.splice(i, 1)
                material_type_section.expanded = false
            }
            else
            {
                // Add it
                materialList.expandedTypes.push(identifier)
                material_type_section.expanded = true
            }
            UM.Preferences.setValue("cura/expanded_types", materialList.expandedTypes.join(";"));
        }
    }
    Column
    {
        height: material_type_section.expanded ? childrenRect.height : 0
        visible: material_type_section.expanded
        width: parent.width
        anchors.top: material_type_header.bottom
        Repeater
        {
            model: colorsModel
            delegate: MaterialsSlot
            {
                material: model
            }
        }
    }

    Connections
    {
        target: UM.Preferences
        onPreferenceChanged:
        {
            if (preference !== "cura/expanded_types" && preference !== "cura/expanded_brands")
            {
                return;
            }

            expanded = materialList.expandedTypes.indexOf(materialBrand + "_" + materialName) > -1
        }
    }
}