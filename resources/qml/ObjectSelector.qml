// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: objectSelector
    width: UM.Theme.getSize("objects_menu_size").width
    property bool opened: UM.Preferences.getValue("cura/show_list_of_objects")

    // Eat up all the mouse events (we don't want the scene to react or have the scene context menu showing up)
    MouseArea
    {
        anchors.fill: parent
        acceptedButtons: Qt.AllButtons
    }

    Button
    {
        id: openCloseButton
        width: parent.width
        height: contentItem.height + bottomPadding
        hoverEnabled: true
        padding: 0
        bottomPadding: UM.Theme.getSize("narrow_margin").height / 2 | 0

        anchors
        {
            bottom: contents.top
            horizontalCenter: parent.horizontalCenter
        }

        contentItem: Item
        {
            width: parent.width
            height: label.height

            UM.RecolorImage
            {
                id: openCloseIcon
                width: UM.Theme.getSize("standard_arrow").width
                height: UM.Theme.getSize("standard_arrow").height
                sourceSize.width: width
                anchors.left: parent.left
                color: openCloseButton.hovered ? UM.Theme.getColor("small_button_text_hover") : UM.Theme.getColor("small_button_text")
                source: objectSelector.opened ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_top")
            }

            Label
            {
                id: label
                anchors.left: openCloseIcon.right
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                text: catalog.i18nc("@label", "Object list")
                font: UM.Theme.getFont("default")
                color: openCloseButton.hovered ? UM.Theme.getColor("small_button_text_hover") : UM.Theme.getColor("small_button_text")
                renderType: Text.NativeRendering
                elide: Text.ElideRight
            }
        }

        background: Item {}

        onClicked:
        {
            UM.Preferences.setValue("cura/show_list_of_objects", !objectSelector.opened)
            objectSelector.opened = UM.Preferences.getValue("cura/show_list_of_objects")
        }
    }

    Rectangle
    {
        id: contents
        width: parent.width
        visible: objectSelector.opened
        height: visible ? listView.height : 0
        color: UM.Theme.getColor("main_background")
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")

        Behavior on height { NumberAnimation { duration: 100 } }

        anchors.bottom: parent.bottom

        ListView
        {
            id: listView
            clip: true
            anchors
            {
                left: parent.left
                right: parent.right
                margins: UM.Theme.getSize("default_lining").width
            }

            ScrollBar.vertical: ScrollBar
            {
                hoverEnabled: true
            }

            property real maximumHeight: UM.Theme.getSize("objects_menu_size").height

            height: Math.min(contentHeight, maximumHeight)

            model: Cura.ObjectsModel {}

            delegate: ObjectItemButton
            {
                id: modelButton
                Binding
                {
                    target: modelButton
                    property: "checked"
                    value: model.selected
                }
                text: model.name
                width: listView.width
                property bool outsideBuildArea: model.outside_build_area
                property int perObjectSettingsCount: model.per_object_settings_count
                property string meshType: model.mesh_type
            }
        }
    }
}
