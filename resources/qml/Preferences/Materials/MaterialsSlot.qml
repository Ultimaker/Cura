// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

// A single material row, typically used in a MaterialsBrandSection

Rectangle
{
    id: materialSlot
    property var material: null
    property var hovered: false
    property var is_favorite: material != null && material.is_favorite

    height: UM.Theme.getSize("favorites_row").height
    width: parent.width
    //color: material != null ? (base.currentItem.root_material_id == material.root_material_id ? UM.Theme.getColor("favorites_row_selected") : "transparent") : "transparent"
    color:
    {
        if(material !== null && base.currentItem !== null)
        {
            if(base.currentItem.root_material_id === material.root_material_id)
            {
                return UM.Theme.getColor("favorites_row_selected")
            }
        }
        return "transparent"
    }
    Rectangle
    {
        id: swatch
        color: material != null ? material.color_code : "transparent"
        border.width: UM.Theme.getSize("default_lining").width
        border.color: "black"
        width: UM.Theme.getSize("favorites_button_icon").width
        height: UM.Theme.getSize("favorites_button_icon").height
        anchors.verticalCenter: materialSlot.verticalCenter
        anchors.left: materialSlot.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
    }
    Label
    {
        text: material != null ? material.brand + " " + material.name : ""
        verticalAlignment: Text.AlignVCenter
        height: parent.height
        anchors.left: swatch.right
        anchors.verticalCenter: materialSlot.verticalCenter
        anchors.leftMargin: UM.Theme.getSize("narrow_margin").width
        font.italic: material != null && Cura.MachineManager.currentRootMaterialId[Cura.ExtruderManager.activeExtruderIndex] == material.root_material_id
    }
    MouseArea
    {
        anchors.fill: parent
        onClicked:
        {
            materialList.currentBrand = material.brand
            materialList.currentType = material.brand + "_" + material.material
            base.setExpandedActiveMaterial(material.root_material_id)
        }
        hoverEnabled: true
        onEntered: { materialSlot.hovered = true }
        onExited: { materialSlot.hovered = false }
    }
    Button
    {
        id: favorite_button
        text: ""
        implicitWidth: UM.Theme.getSize("favorites_button").width
        implicitHeight: UM.Theme.getSize("favorites_button").height
        visible: materialSlot.hovered || materialSlot.is_favorite || favorite_button.hovered
        anchors
        {
            right: materialSlot.right
            verticalCenter: materialSlot.verticalCenter
        }
        onClicked:
        {
            if (materialSlot.is_favorite)
            {
                CuraApplication.getMaterialManagementModel().removeFavorite(material.root_material_id)
            }
            else
            {
                CuraApplication.getMaterialManagementModel().addFavorite(material.root_material_id)
            }
        }
        style: ButtonStyle
        {
            background: Item { }
        }
        UM.RecolorImage
        {
            anchors
            {
                verticalCenter: favorite_button.verticalCenter
                horizontalCenter: favorite_button.horizontalCenter
            }
            width: UM.Theme.getSize("favorites_button_icon").width
            height: UM.Theme.getSize("favorites_button_icon").height
            color:
            {
                if (favorite_button.hovered)
                {
                    return UM.Theme.getColor("primary_hover")
                }
                else
                {
                    if (materialSlot.is_favorite)
                    {
                        return UM.Theme.getColor("primary")
                    }
                    else
                    {
                        UM.Theme.getColor("text_inactive")
                    }
                }
            }
            source: materialSlot.is_favorite ? UM.Theme.getIcon("StarFilled") : UM.Theme.getIcon("Star")
        }
    }
}
