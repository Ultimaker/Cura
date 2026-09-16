// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.9
import QtQuick.Layouts 2.10

import UM 1.5 as UM
import Cura 1.0 as Cura

Rectangle
{
    property alias name: printerTitle.text
    property string unique_id
    property var extruders
    property var manager


    width: parent.width
    height: childrenRect.height + 2 * UM.Theme.getSize("default_margin").height

    color: UM.Theme.getColor("background_1")
    border.color: UM.Theme.getColor("border_main")
    border.width: UM.Theme.getSize("default_lining").width

    RowLayout
    {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.margins: UM.Theme.getSize("default_margin").width

        Cura.IconWithText
        {
            id: printerTitle

            Layout.preferredWidth: parent.width / 3
            Layout.preferredHeight: childrenRect.height
            Layout.fillWidth: true
            Layout.alignment: extruders[0].materials.length > 1 ? Qt.AlignTop : Qt.AlignCenter
            Layout.fillHeight: false

            source: UM.Theme.getIcon("Printer")
            spacing: UM.Theme.getSize("thin_margin").width
            iconSize: UM.Theme.getSize("medium_button_icon").width
            font: UM.Theme.getFont("medium_bold")
        }

        Column
        {
            id: extruderInformation
            Layout.fillWidth: true
            Layout.preferredWidth: parent.width / 2
            Layout.preferredHeight: childrenRect.height
            Layout.alignment: extruders[0].materials.length > 1 ? Qt.AlignTop : Qt.AlignCenter
            spacing: UM.Theme.getSize("narrow_margin").height

            Repeater
            {
                model: extruders

                Item
                {
                    width: extruderInformation.width
                    height: childrenRect.height

                    Cura.ExtruderIcon
                    {
                        id: extruderIcon
                        anchors.top: parent.top
                        anchors.left: parent.left
                        materialColor: modelData.materials.length == 1 ? modelData.materials[0].hexcolor : "white"
                        iconSize: UM.Theme.getSize("medium_button_icon").width
                    }

                    UM.Label
                    {
                        id: extruderCore
                        anchors.verticalCenter: extruderIcon.verticalCenter
                        anchors.left: extruderIcon.right
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        text: modelData ? (modelData.core ? modelData.core : "" ) : ""
                        font: UM.Theme.getFont("default_bold")
                    }

                    UM.Label
                    {
                        id: singleMaterialText
                        anchors.left: extruderCore.right
                        anchors.right: parent.right
                        anchors.verticalCenter: extruderCore.verticalCenter
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        text: modelData.materials.length == 1 ? `${modelData.materials[0].brand} ${modelData.materials[0].name}` : ""
                        visible: modelData.materials.length == 1
                    }
                    ColumnLayout
                    {
                        id: multiMaterialText
                        anchors.top: extruderCore.bottom
                        anchors.left: extruderCore.left
                        anchors.topMargin: UM.Theme.getSize("narrow_margin").height
                        visible: modelData.materials.length > 1
                        Repeater
                        {
                            model: modelData.materials.length > 1 ? modelData.materials: null
                            UM.Label
                            {
                                text: `${modelData.brand} ${modelData.name}`
                            }
                        }
                    }
                }
            }
        }

        Button
        {
            id: printButton

            implicitWidth: UM.Theme.getSize("large_button").width
            implicitHeight: implicitWidth
            Layout.alignment: extruders[0].materials.length > 1 ? Qt.AlignTop : Qt.AlignCenter
            Layout.preferredHeight: childrenRect.height
            padding: 0

            background: Rectangle
            {
                border.width: UM.Theme.getSize("default_lining").width
                border.color: UM.Theme.getColor("border_accent_1")
                color: printButton.hovered ? UM.Theme.getColor("toolbar_button_hover"): UM.Theme.getColor("background_1")
            }

            contentItem: Item
            {
                UM.ColorImage
                {
                    anchors.centerIn: parent
                    source: UM.Theme.getIcon("Printer")
                    color: UM.Theme.getColor("border_accent_1")
                    width: UM.Theme.getSize("medium_button_icon").width
                    height: width
                }
            }

            onClicked: manager.printerSelected(unique_id)
        }
    }
}
