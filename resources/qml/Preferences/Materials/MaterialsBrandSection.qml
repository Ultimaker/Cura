// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: brand_section

    property var sectionName: ""
    property var elementsModel   // This can be a MaterialTypesModel or GenericMaterialsModel or FavoriteMaterialsModel
    property var hasMaterialTypes: true  // It indicates wheather it has material types or not
    property var expanded: materialList.expandedBrands.indexOf(sectionName) > -1

    height: childrenRect.height
    width: parent.width
    Rectangle
    {
        id: brand_header_background
        color:
        {
            if(!expanded && sectionName == materialList.currentBrand)
            {
                return UM.Theme.getColor("favorites_row_selected")
            }
            else
            {
                return UM.Theme.getColor("favorites_header_bar")
            }
        }
        anchors.fill: brand_header
    }
    Row
    {
        id: brand_header
        width: parent.width
        Label
        {
            id: brand_name
            text: sectionName
            height: UM.Theme.getSize("favorites_row").height
            width: parent.width - UM.Theme.getSize("favorites_button").width
            verticalAlignment: Text.AlignVCenter
            leftPadding: (UM.Theme.getSize("default_margin").width / 2) | 0
        }
        Button
        {
            text: ""
            implicitWidth: UM.Theme.getSize("favorites_button").width
            implicitHeight: UM.Theme.getSize("favorites_button").height
            UM.RecolorImage
            {
                anchors
                {
                    verticalCenter: parent.verticalCenter
                    horizontalCenter: parent.horizontalCenter
                }
                width: UM.Theme.getSize("standard_arrow").width
                height: UM.Theme.getSize("standard_arrow").height
                color: "black"
                source: brand_section.expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
            }
            style: ButtonStyle
            {
                background: Item { }
            }
        }
    }
    MouseArea
    {
        anchors.fill: brand_header
        onPressed:
        {
            const i = materialList.expandedBrands.indexOf(sectionName)
            if (i > -1)
            {
                // Remove it
                materialList.expandedBrands.splice(i, 1)
                brand_section.expanded = false
            }
            else
            {
                // Add it
                materialList.expandedBrands.push(sectionName)
                brand_section.expanded = true
            }
            UM.Preferences.setValue("cura/expanded_brands", materialList.expandedBrands.join(";"));
        }
    }
    Column
    {
        id: brandMaterialList
        anchors.top: brand_header.bottom
        width: parent.width
        anchors.left: parent.left
        height: brand_section.expanded ? childrenRect.height : 0
        visible: brand_section.expanded

        Repeater
        {
            model: elementsModel
            delegate: Loader
            {
                id: loader
                width: parent.width
                property var element: model
                sourceComponent: hasMaterialTypes ? materialsTypeSection : materialSlot
            }
        }
    }

    Component
    {
        id: materialsTypeSection
        MaterialsTypeSection
        {
            materialType: element
        }
    }

    Component
    {
        id: materialSlot
        MaterialsSlot
        {
            material: element
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

            expanded = materialList.expandedBrands.indexOf(sectionName) > -1
        }
    }
}