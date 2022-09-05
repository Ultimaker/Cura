import QtQuick 2.2
import QtQuick.Controls 2.9
import QtQuick.Layouts 2.10

import UM 1.5 as UM
import Cura 1.0 as Cura

Rectangle {
    property alias name: printerTitle.text
    property var extruders

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
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            Layout.fillHeight: false

            source: UM.Theme.getIcon("Printer")
            spacing: UM.Theme.getSize("thin_margin").width
            iconSize: UM.Theme.getSize("medium_button_icon").width
            font: UM.Theme.getFont("medium_bold")
        }

        ColumnLayout
        {
            id: extruderInformation
            Layout.fillWidth: true
            Layout.preferredWidth: parent.width / 2
            Layout.alignment: Qt.AlignTop
            spacing: UM.Theme.getSize("default_margin").width

            Repeater
            {
                model: extruders

                Item
                {
                    height: childrenRect.height

                    Cura.ExtruderIcon
                    {
                        id: extruderIcon
                        anchors.top: parent.top
                        anchors.left: parent.left
                        materialColor: modelData.materials.length == 1 ? modelData.materials[0].color : "white"
                        iconSize: UM.Theme.getSize("medium_button_icon").width
                    }

                    UM.Label
                    {
                        id: extruderCore
                        anchors.verticalCenter: extruderIcon.verticalCenter
                        anchors.left: extruderIcon.right
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        text: modelData.core
                        font: UM.Theme.getFont("default_bold")
                    }

                    UM.Label
                    {
                        id: singleMaterialText
                        anchors.left: extruderCore.right
                        anchors.verticalCenter: extruderCore.verticalCenter
                        text: modelData.materials.length == 1 ? modelDatamaterials[0].name : "test"
                        visible: modelData.materials.length == 1
                    }

                    ColumnLayout
                    {
                        id: multiMaterialText
                        anchors.top: extruderCore.bottom
                        anchors.left: extruderCore.left
                        anchors.topMargin: UM.Theme.getSize("narrow_margin").height
                        Repeater
                        {
                            model: modelData.materials
                            visible: modelData.materials.length > 1
                            UM.Label
                            {
                                text: modelData.name
                            }
                        }
                    }
                }
            }
        }

        Button
        {
            id: printButton

            implicitWidth: UM.Theme.getSize("medium_button").width
            implicitHeight: implicitWidth
            Layout.alignment: Qt.AlignTop
            padding: 0

            background: Rectangle
            {
                border.width: UM.Theme.getSize("default_lining").width
                border.color: UM.Theme.getColor("border_accent_1")
                color: control.hovered ? UM.Theme.getColor("toolbar_button_hover"): UM.Theme.getColor("background_1")
            }

            contentItem: Item
            {
                UM.ColorImage
                {
                    anchors.centerIn: parent
                    source: UM.Theme.getIcon("Printer")
                    color: UM.Theme.getColor("border_accent_1")
                    width: UM.Theme.getSize("small_button_icon").width
                    height: width
                }
            }
        }
    }
}