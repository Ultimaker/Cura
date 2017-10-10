// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura

Button
{
    id: base

    property var extruder;

    text: catalog.i18ncp("@label %1 is filled in with the name of an extruder", "Print Selected Model with %1", "Print Selected Models with %1", UM.Selection.selectionCount).arg(extruder.name)

    style: UM.Theme.styles.tool_button;
    iconSource: UM.Theme.getIcon("extruder_button")

    checked: ExtruderManager.selectedObjectExtruders.indexOf(extruder.id) != -1
    enabled: UM.Selection.hasSelection

    property color customColor: base.hovered ? UM.Theme.getColor("button_hover") : UM.Theme.getColor("button");

    Rectangle
    {
        anchors.fill: parent
        anchors.margins: UM.Theme.getSize("default_lining").width;

        color: "transparent"

        border.width: base.checked ? UM.Theme.getSize("default_lining").width : 0;
        border.color: UM.Theme.getColor("button_text")
    }

    Item
    {
        anchors.centerIn: parent
        width: UM.Theme.getSize("default_margin").width
        height: UM.Theme.getSize("default_margin").height

        Text
        {
            anchors.centerIn: parent;
            text: index + 1;
            color: parent.enabled ? UM.Theme.getColor("button_text") : UM.Theme.getColor("button_disabled_text")
            font: UM.Theme.getFont("default_bold");
        }
    }

    // Material colour circle
    // Only draw the filling colour of the material inside the SVG border.
    Rectangle
    {
        anchors
        {
            right: parent.right
            top: parent.top
            rightMargin: UM.Theme.getSize("extruder_button_material_margin").width
            topMargin: UM.Theme.getSize("extruder_button_material_margin").height
        }

        color: model.color

        width: UM.Theme.getSize("extruder_button_material").width
        height: UM.Theme.getSize("extruder_button_material").height
        radius: width / 2

        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("extruder_button_material_border")

        opacity: !base.enabled ? 0.2 : 1.0
    }

    onClicked:
    {
        forceActiveFocus() //First grab focus, so all the text fields are updated
        CuraActions.setExtruderForSelection(extruder.id);
    }
}
