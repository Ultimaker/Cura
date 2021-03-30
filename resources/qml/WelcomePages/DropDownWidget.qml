// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This is the dropdown list widget in the welcome wizard. The dropdown list has a header bar which is always present,
// and its content whose visibility can be toggled by clicking on the header bar. The content is displayed as an
// expandable dropdown box that will appear below the header bar.
//
// The content is configurable via the property "contentComponent", which will be loaded by a Loader when set.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    id: base

    implicitWidth: 200 * screenScaleFactor
    height: header.contentShown ? (header.height + contentRectangle.height) : header.height

    property var contentComponent: null
    property alias contentItem: contentLoader.item

    property alias title: header.title
    property bool contentShown: false  // indicates if this dropdown widget is expanded to show its content

    signal clicked()

    Connections
    {
        target: header
        function onClicked()
        {
            base.contentShown = !base.contentShown
            clicked()
        }
    }

    DropDownHeader
    {
        id: header
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: UM.Theme.getSize("expandable_component_content_header").height
        rightIconSource: contentShown ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_left")
        contentShown: base.contentShown
    }

    Cura.RoundedRectangle
    {
        id: contentRectangle
        // Move up a bit (exaclty the width of the border) to avoid double line
        y: header.height - UM.Theme.getSize("default_lining").width
        anchors.left: header.left
        anchors.right: header.right
        // Add 2x lining, because it needs a bit of space on the top and the bottom.
        height: contentLoader.item.height + 2 * UM.Theme.getSize("thick_lining").height

        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")
        color: UM.Theme.getColor("main_background")
        radius: UM.Theme.getSize("default_radius").width
        visible: base.contentShown
        cornerSide: Cura.RoundedRectangle.Direction.Down

        Loader
        {
            id: contentLoader
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right
            // Keep a small margin with the Rectangle container so its content will not overlap with the Rectangle
            // border.
            anchors.margins: UM.Theme.getSize("default_lining").width
            sourceComponent: base.contentComponent != null ? base.contentComponent : emptyComponent
        }

        // This is the empty component/placeholder that will be shown when the widget gets expanded.
        // It contains a text line "Empty"
        Component
        {
            id: emptyComponent

            Label
            {
                text: catalog.i18nc("@label", "Empty")
                height: UM.Theme.getSize("action_button").height
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font: UM.Theme.getFont("medium")
                renderType: Text.NativeRendering
            }
        }
    }
}
