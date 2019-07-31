// Copyright (c) 2019 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4

import UM 1.1 as UM

Item
{
    id: base

    property var packageData
    property var technicalDataSheetUrl: packageData.links.technicalDataSheet
    property var safetyDataSheetUrl: packageData.links.safetyDataSheet
    property var printingGuidelinesUrl: packageData.links.printingGuidelines
    property var materialWebsiteUrl: packageData.links.website

    height: childrenRect.height
    onVisibleChanged: packageData.type === "material" && (compatibilityItem.visible || dataSheetLinks.visible)

    Column
    {
        id: compatibilityItem
        visible: packageData.has_configs
        width: parent.width
        // This is a bit of a hack, but the whole QML is pretty messy right now. This needs a big overhaul.
        height: visible ? heading.height + table.height: 0

        Label
        {
            id: heading
            width: parent.width
            text: catalog.i18nc("@label", "Compatibility")
            wrapMode: Text.WordWrap
            color: UM.Theme.getColor("text_medium")
            font: UM.Theme.getFont("medium")
            renderType: Text.NativeRendering
        }

        TableView
        {
            id: table
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
                color: UM.Theme.getColor("main_background")
                height: UM.Theme.getSize("toolbox_chart_row").height
                Label
                {
                    anchors.verticalCenter: parent.verticalCenter
                    elide: Text.ElideRight
                    text: styleData.value || ""
                    color: UM.Theme.getColor("text")
                    font: UM.Theme.getFont("default_bold")
                    renderType: Text.NativeRendering
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
                    renderType: Text.NativeRendering
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
                    renderType: Text.NativeRendering
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
                    renderType: Text.NativeRendering
                }
            }

            TableViewColumn
            {
                role: "machine"
                title: catalog.i18nc("@label:table_header", "Machine")
                width: Math.floor(table.width * 0.25)
                delegate: columnTextDelegate
            }
            TableViewColumn
            {
                role: "print_core"
                title: catalog.i18nc("@label:table_header", "Print Core")
                width: Math.floor(table.width * 0.2)
            }
            TableViewColumn
            {
                role: "build_plate"
                title: catalog.i18nc("@label:table_header", "Build Plate")
                width: Math.floor(table.width * 0.225)
            }
            TableViewColumn
            {
                role: "support_material"
                title: catalog.i18nc("@label:table_header", "Support")
                width: Math.floor(table.width * 0.225)
            }
            TableViewColumn
            {
                role: "quality"
                title: catalog.i18nc("@label:table_header", "Quality")
                width: Math.floor(table.width * 0.1)
            }
        }
    }

    Label
    {
        id: dataSheetLinks
        anchors.top: compatibilityItem.bottom
        anchors.topMargin: UM.Theme.getSize("narrow_margin").height
        visible: base.technicalDataSheetUrl !== undefined ||
                    base.safetyDataSheetUrl !== undefined ||
                    base.printingGuidelinesUrl !== undefined ||
                    base.materialWebsiteUrl !== undefined
                    
        text:
        {
            var result = ""
            if (base.technicalDataSheetUrl !== undefined)
            {
                var tds_name = catalog.i18nc("@action:label", "Technical Data Sheet")
                result += "<a href='%1'>%2</a>".arg(base.technicalDataSheetUrl).arg(tds_name)
            }
            if (base.safetyDataSheetUrl !== undefined)
            {
                if (result.length > 0)
                {
                    result += "<br/>"
                }
                var sds_name = catalog.i18nc("@action:label", "Safety Data Sheet")
                result += "<a href='%1'>%2</a>".arg(base.safetyDataSheetUrl).arg(sds_name)
            }
            if (base.printingGuidelinesUrl !== undefined)
            {
                if (result.length > 0)
                {
                    result += "<br/>"
                }
                var pg_name = catalog.i18nc("@action:label", "Printing Guidelines")
                result += "<a href='%1'>%2</a>".arg(base.printingGuidelinesUrl).arg(pg_name)
            }
            if (base.materialWebsiteUrl !== undefined)
            {
                if (result.length > 0)
                {
                    result += "<br/>"
                }
                var pg_name = catalog.i18nc("@action:label", "Website")
                result += "<a href='%1'>%2</a>".arg(base.materialWebsiteUrl).arg(pg_name)
            }

            return result
        }
        font: UM.Theme.getFont("default")
        color: UM.Theme.getColor("text")
        linkColor: UM.Theme.getColor("text_link")
        onLinkActivated: Qt.openUrlExternally(link)
        renderType: Text.NativeRendering
    }
}
