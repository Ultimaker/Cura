// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.5 as Cura

// A single material row, typically used in a MaterialsBrandSection

Rectangle
{
    id: materialSlot
    property var material: null
    property var hovered: false
    property var is_favorite: material != null && material.is_favorite

    height: UM.Theme.getSize("favorites_row").height
    width: parent.width
    color:
    {
        if (material !== null && base.currentItem !== null)
        {
            if (base.currentItem.root_material_id === material.root_material_id)
            {
                return UM.Theme.getColor("favorites_row_selected");
            }
        }
        return "transparent";
    }
    Rectangle
    {
        id: swatch
        color: material != null ? material.color_code : "transparent"
        width: UM.Theme.getSize("icon_indicator").width
        height: UM.Theme.getSize("icon_indicator").height
        radius: width / 2
        anchors.verticalCenter: materialSlot.verticalCenter
        anchors.left: materialSlot.left
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
    }
    UM.Label
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
