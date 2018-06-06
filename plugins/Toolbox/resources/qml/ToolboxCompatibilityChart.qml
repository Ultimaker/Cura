// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    property var packageData
    anchors.topMargin: UM.Theme.getSize("default_margin").height
    height: visible ? childrenRect.height : 0
    visible: packageData.type == "material" && packageData.has_configs
    Label
    {
        id: heading
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        text: catalog.i18nc("@label", "Compatibility")
        wrapMode: Text.WordWrap
        color: UM.Theme.getColor("text_medium")
        font: UM.Theme.getFont("medium")
    }
    TableView
    {
        id: table
        anchors.top: heading.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        frameVisible: false
        selectionMode: 0
        model: packageData.supported_configs
        headerDelegate: Rectangle
        {
            color: UM.Theme.getColor("sidebar")
            height: UM.Theme.getSize("toolbox_chart_row").height
            Label
            {
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
                text: styleData.value || ""
                color: UM.Theme.getColor("text")
                font: UM.Theme.getFont("default_bold")
            }
            Rectangle
            {
                anchors.bottom: parent.bottom
                height: UM.Theme.getSize("default_lining").height
                width: parent.width
                color: "black"
            }
        }
        rowDelegate: Item
        {
            height: UM.Theme.getSize("toolbox_chart_row").height
            Label
            {
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
                text: styleData.value || ""
                color: UM.Theme.getColor("text_medium")
                font: UM.Theme.getFont("default")
            }
        }
        itemDelegate: Item
        {
            height: UM.Theme.getSize("toolbox_chart_row").height
            Label
            {
                anchors.verticalCenter: parent.verticalCenter
                elide: Text.ElideRight
                text: styleData.value || ""
                color: UM.Theme.getColor("text_medium")
                font: UM.Theme.getFont("default")
            }
        }

        TableViewColumn
        {
            role: "machine"
            title: "Machine"
            width: Math.floor(table.width * 0.25)
        }
        TableViewColumn
        {
            role: "print_core"
            title: "Print Core"
            width: Math.floor(table.width * 0.2)
        }
        TableViewColumn
        {
            role: "build_plate"
            title: "Build Plate"
            width: Math.floor(table.width * 0.225)
        }
        TableViewColumn
        {
            role: "support_material"
            title: "Support"
            width: Math.floor(table.width * 0.225)
        }
        TableViewColumn
        {
            role: "quality"
            title: "Quality"
            width: Math.floor(table.width * 0.1)
        }
    }
}
