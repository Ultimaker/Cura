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
    id: material_slot
    property var material
    property var hovered: false
    property var is_favorite: material.is_favorite

    height: UM.Theme.getSize("favorites_row").height
    width: parent.width
    color: base.currentItem == model ? UM.Theme.getColor("favorites_row_selected") : "transparent"
    
    Item
    {
        height: parent.height
        width: parent.width
        Rectangle
        {
            id: swatch
            color: material.color_code
            border.width: UM.Theme.getSize("default_lining").width
            border.color: "black"
            width: UM.Theme.getSize("favorites_button_icon").width
            height: UM.Theme.getSize("favorites_button_icon").height
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
        }
        Label
        {
            text: material.brand + " " + material.name
            verticalAlignment: Text.AlignVCenter
            height: parent.height
            anchors.left: swatch.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.leftMargin: UM.Theme.getSize("narrow_margin").width
        }
        MouseArea
        {
            anchors.fill: parent
            onClicked: { base.currentItem = material }
            hoverEnabled: true
            onEntered: { material_slot.hovered = true }
            onExited: { material_slot.hovered = false }
        }
        Button
        {
            id: favorite_button
            text: ""
            implicitWidth: UM.Theme.getSize("favorites_button").width
            implicitHeight: UM.Theme.getSize("favorites_button").height
            visible: material_slot.hovered || material_slot.is_favorite || favorite_button.hovered
            anchors
            {
                right: parent.right
                verticalCenter: parent.verticalCenter
            }
            onClicked:
            {
                if (material_slot.is_favorite) {
                    base.materialManager.removeFavorite(material.root_material_id)
                    material_slot.is_favorite = false
                    return
                }
                base.materialManager.addFavorite(material.root_material_id)
                material_slot.is_favorite = true
                return
            }
            style: ButtonStyle
            {
                background: Rectangle
                {
                    anchors.fill: parent
                    color: "transparent"
                }
            }
            UM.RecolorImage {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                    horizontalCenter: parent.horizontalCenter
                }
                width: UM.Theme.getSize("favorites_button_icon").width
                height: UM.Theme.getSize("favorites_button_icon").height
                sourceSize.width: width
                sourceSize.height: height
                color:
                {
                    if (favorite_button.hovered)
                    {
                        return UM.Theme.getColor("primary_hover")
                    }
                    else
                    {
                        if (material_slot.is_favorite)
                        {
                            return UM.Theme.getColor("primary")
                        }
                        else
                        {
                            UM.Theme.getColor("text_inactive")
                        }
                    }
                }
                source: material_slot.is_favorite ? UM.Theme.getIcon("favorites_star_full") : UM.Theme.getIcon("favorites_star_empty")
            }
        }
    }
}