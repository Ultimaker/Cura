// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: base

    property var packageData
    property var technicalDataSheetUrl: {
        var link = undefined
        if ("Technical Data Sheet" in packageData.links)
        {
            link = packageData.links["Technical Data Sheet"]
        }
        return link
    }

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

        // Workaround for scroll issues (QTBUG-49652)
        flickableItem.interactive: false
        Component.onCompleted:
        {
            for (var i = 0; i < flickableItem.children.length; ++i)
            {
                flickableItem.children[i].enabled = false
            }
        }
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

        Component
        {
            id: columnTextDelegate
            Label
            {
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                text: styleData.value || ""
                elide: Text.ElideRight
                color: UM.Theme.getColor("text_medium")
                font: UM.Theme.getFont("default")
            }
        }

        TableViewColumn
        {
            role: "machine"
            title: "Machine"
            width: Math.floor(table.width * 0.25)
            delegate: columnTextDelegate
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

    Label
    {
        id: technical_data_sheet
        anchors.top: table.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height / 2
        visible: base.technicalDataSheetUrl !== undefined
        text:
        {
            if (base.technicalDataSheetUrl !== undefined)
            {
                return "<a href='%1'>%2</a>".arg(base.technicalDataSheetUrl).arg("Technical Data Sheet")
            }
            return ""
        }
        font: UM.Theme.getFont("very_small")
        color: UM.Theme.getColor("text")
        linkColor: UM.Theme.getColor("text_link")
        onLinkActivated: Qt.openUrlExternally(link)
    }

}
