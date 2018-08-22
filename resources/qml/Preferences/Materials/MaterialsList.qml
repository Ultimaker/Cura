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
    id: materialList
    width: materialScrollView.width - 17
    height: childrenRect.height

    // Children
    UM.I18nCatalog { id: catalog; name: "cura"; }
    Cura.BrandMaterialsModel { id: materialsModel }
    Cura.FavoriteMaterialsModel { id: favoriteMaterialsModel }
    Cura.GenericMaterialsModel { id: genericMaterialsModel }
    Column
    {
        Rectangle
        {
            property var expanded: true

            id: favorites_section
            height: childrenRect.height
            width: materialList.width
            Rectangle
            {
                id: favorites_header_background
                color: UM.Theme.getColor("favorites_header_bar")
                anchors.fill: favorites_header
            }
            Row
            {
                id: favorites_header
                Label
                {
                    id: favorites_name
                    text: "Favorites"
                    height: UM.Theme.getSize("favorites_row").height
                    width: materialList.width - UM.Theme.getSize("favorites_button").width
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
                        source: favorites_section.expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
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
                anchors.fill: favorites_header
                onPressed:
                {
                    favorites_section.expanded = !favorites_section.expanded
                }
            }
            Column
            {
                anchors.top: favorites_header.bottom
                anchors.left: parent.left
                width: materialList.width
                height: favorites_section.expanded ? childrenRect.height : 0
                visible: favorites_section.expanded
                Repeater
                {
                    model: favoriteMaterialsModel
                    delegate: MaterialSlot {
                        material: model
                    }
                }
            }
        }
        Rectangle
        {
            property var expanded: true

            id: generic_section
            height: childrenRect.height
            width: materialList.width
            Rectangle
            {
                id: generic_header_background
                color: UM.Theme.getColor("favorites_header_bar")
                anchors.fill: generic_header
            }
            Row
            {
                id: generic_header
                Label
                {
                    id: generic_name
                    text: "Generic"
                    height: UM.Theme.getSize("favorites_row").height
                    width: materialList.width - UM.Theme.getSize("favorites_button").width
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
                        source: generic_section.expanded ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
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
                anchors.fill: generic_header
                onPressed:
                {
                    generic_section.expanded = !generic_section.expanded
                }
            }
            Column
            {
                anchors.top: generic_header.bottom
                width: materialList.width
                anchors.left: parent.left
                height: generic_section.expanded ? childrenRect.height : 0
                visible: generic_section.expanded
                Repeater
                {
                    model: genericMaterialsModel
                    delegate: MaterialSlot {
                        material: model
                    }
                }
            }
        }
        Repeater
        {
            id: brand_list

            model: materialsModel
            delegate: Rectangle
            {
                id: brand_section
                property var expanded: true
                property var types_model: model.materials
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
                        delegate: Rectangle
                        {
                            id: material_type_section
                            property var expanded: true
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
                                    material_type_section.expanded = !material_type_section.expanded
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
                                    delegate: MaterialSlot {
                                        material: model
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}