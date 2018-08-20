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
    UM.I18nCatalog { id: catalog; name: "cura"; }
    Cura.BrandMaterialsModel { id: materialsModel }
    Cura.GenericMaterialsModel { id: genericMaterialsModel }

    width: materialScrollView.width - 20
    height: childrenRect.height


    Column
    {
        Rectangle
        {
            height: 23
            width: materialList.width
            Label
            {
                text: "Generic"
            }
        }
        Repeater
        {
            model: genericMaterialsModel
            delegate: Rectangle
            {
                height: 23
                width: materialList.width
                color: "green"
                Label
                {
                    text: model.name
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
                    color: "grey"
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
                        height: 24
                        width: parent.width - 24
                        verticalAlignment: Text.AlignVCenter
                        leftPadding: 4
                    }
                    Button
                    {
                        text: ""
                        implicitWidth: 24
                        implicitHeight: 24
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
                    width: parent.width - leftPadding
                    anchors.left: parent.left
                    leftPadding: 8
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
                                color: "grey"
                                anchors.bottom: material_type_header.bottom
                                height: 1
                                width: parent.width
                            }
                            Row
                            {
                                id: material_type_header
                                width: parent.width

                                Label
                                {
                                    text: model.name
                                    height: 24
                                    width: parent.width - 24
                                    id: material_type_name
                                    verticalAlignment: Text.AlignVCenter
                                }
                                Button
                                {
                                    text: ""
                                    implicitWidth: 24
                                    implicitHeight: 24
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
                                width: parent.width - leftPadding
                                anchors.top: material_type_header.bottom
                                leftPadding: 8
                                anchors.left: parent.left
                                Repeater
                                {
                                    model: colors_model
                                    delegate: Rectangle
                                    {
                                        height: 24
                                        width: parent.width
//                                        color: "green"
                                        Row
                                        {
                                            height: parent.height
                                            width: parent.width
                                            Rectangle
                                            {
                                                id: swatch
                                                color: model.color_code
                                                border.width: 1
                                                border.color: "black"
                                                width: 14
                                                height: 14
                                                anchors.verticalCenter: parent.verticalCenter
                                            }
                                            Label
                                            {
                                                text: model.name
                                                verticalAlignment: Text.AlignVCenter
                                                height: 24
                                                anchors.left: swatch.right
                                                anchors.verticalCenter: parent.verticalCenter
                                                anchors.leftMargin: 4
                                            }
                                            MouseArea
                                            {
                                                anchors.fill: parent
                                                onClicked:
                                                {
                                                    print(model.guid)
                                                }
                                            }
                                            Button
                                            {
                                                text: "+"
                                                implicitWidth: 24
                                                implicitHeight: 24
                                                anchors.right: parent.right
                                                anchors.verticalCenter: parent.verticalCenter
                                                onClicked:
                                                {
                                                    if (model.is_favorite) {
                                                        base.materialManager.removeFavorite(model.root_material_id)
                                                        model.is_favorite = false
                                                        return
                                                    }
                                                    base.materialManager.addFavorite(model.root_material_id)
                                                    model.is_favorite = true
                                                    return
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
        }
    }
}