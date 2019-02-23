// Copyright (c) 2018 Ultimaker B.V.
// Toolbox is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.1 as UM

Item
{
    id: base

    property var packageData
    property var technicalDataSheetUrl:
    {
        var link = undefined
        if ("Technical Data Sheet" in packageData.links)
        {
            // HACK: This is the way the old API (used in 3.6-beta) used to do it. For safety it's still here,
            // but it can be removed over time.
            link = packageData.links["Technical Data Sheet"]
        }
        else if ("technicalDataSheet" in packageData.links)
        {
            link = packageData.links["technicalDataSheet"]
        }
        return link
    }
    property var safetyDataSheetUrl:
    {
        var sds_name = "safetyDataSheet"
        return (sds_name in packageData.links) ? packageData.links[sds_name] : undefined
    }
    property var printingGuidelinesUrl:
    {
        var pg_name = "printingGuidelines"
        return (pg_name in packageData.links) ? packageData.links[pg_name] : undefined
    }

    property var materialWebsiteUrl:
    {
        var pg_name = "website"
        return (pg_name in packageData.links) ? packageData.links[pg_name] : undefined
    }
    anchors.topMargin: UM.Theme.getSize("default_margin").height
    height: visible ? childrenRect.height : 0

    visible: packageData.type == "material" &&
        (packageData.has_configs || technicalDataSheetUrl !== undefined ||
            safetyDataSheetUrl !== undefined || printingGuidelinesUrl !== undefined ||
            materialWebsiteUrl !== undefined)

    Item
    {
        id: combatibilityItem
        visible: packageData.has_configs
        width: parent.width
        // This is a bit of a hack, but the whole QML is pretty messy right now. This needs a big overhaul.
        height: visible ? heading.height + table.height: 0

        Label
        {
            id: heading
            anchors.topMargin: UM.Theme.getSize("default_margin").height
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
    }

    Label
    {
        id: data_sheet_links
        anchors.top: combatibilityItem.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height / 2
        visible: base.technicalDataSheetUrl !== undefined ||
            base.safetyDataSheetUrl !== undefined || base.printingGuidelinesUrl !== undefined ||
            base.materialWebsiteUrl !== undefined
        height: visible ? contentHeight : 0
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
