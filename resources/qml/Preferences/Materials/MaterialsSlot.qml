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
    property bool hovered: false
    property bool isActive: material != null && Cura.MachineManager.currentRootMaterialId[Cura.ExtruderManager.activeExtruderIndex] == material.root_material_id

    height: UM.Theme.getSize("preferences_page_list_item").height
    width: parent.width
    color: UM.Theme.getColor("main_background")

    states:
    [
        State
        {
            name: "selected"
            when: material !== null && base.currentItem !== null && base.currentItem.root_material_id === material.root_material_id
            PropertyChanges { target: materialSlot; color: UM.Theme.getColor("background_3") }
        },
        State
        {
            name: "hovered"
            when: hovered
            PropertyChanges { target: materialSlot; color: UM.Theme.getColor("background_3") }
        }
    ]

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
        id: materialLabel
        text: material != null ? `${material.brand} ${material.name}` : ""
        font: isActive ? UM.Theme.getFont("default_italic") : UM.Theme.getFont("default")
        elide: Text.ElideRight
        wrapMode: Text.NoWrap
        verticalAlignment: Text.AlignVCenter
        anchors.left: swatch.right
        anchors.right: favoriteButton.visible ? favoriteButton.left : parent.right
        anchors.leftMargin: UM.Theme.getSize("default_margin").width
        anchors.rightMargin: UM.Theme.getSize("narrow_margin").width
        anchors.verticalCenter: materialSlot.verticalCenter
    }

    UM.TooltipArea
    {
        anchors.fill: parent
        text: material != null ? `${material.brand} ${material.name}` : ""
        acceptedButtons: Qt.LeftButton
        onClicked:
        {
            materialList.currentBrand = material.brand;
            materialList.currentType = `${material.brand}_${material.material}`;
            base.setExpandedActiveMaterial(material.root_material_id);
        }
        hoverEnabled: true
        onEntered: { materialSlot.hovered = true }
        onExited: { materialSlot.hovered = false }
    }

    Item
    {
        id: favoriteButton

        states:
        [
            State
            {
                name: "favorite"
                when: material !== null && material.is_favorite
                PropertyChanges { target: favoriteIndicator; source: UM.Theme.getIcon("StarFilled");}
                PropertyChanges { target: favoriteButton; visible: true }
            },
            State
            {
                name: "hovered"
                when: hovered
                PropertyChanges { target: favoriteButton; visible: true }
            }
        ]

        implicitHeight: parent.height
        implicitWidth: favoriteIndicator.width
        anchors.right: materialSlot.right
        visible: false

        UM.ColorImage
        {
            id: favoriteIndicator
            anchors.centerIn: parent
            width: UM.Theme.getSize("small_button_icon").width
            height: UM.Theme.getSize("small_button_icon").height
            color: UM.Theme.getColor("primary")
            source: UM.Theme.getIcon("Star")
        }

        MouseArea
        {
            anchors.fill: parent
            onClicked:
            {
                if (material !== null)
                {
                    if (material.is_favorite)
                    {
                        CuraApplication.getMaterialManagementModel().removeFavorite(material.root_material_id)
                    }
                    else
                    {
                        CuraApplication.getMaterialManagementModel().addFavorite(material.root_material_id)
                    }
                }
            }
        }
    }
}
