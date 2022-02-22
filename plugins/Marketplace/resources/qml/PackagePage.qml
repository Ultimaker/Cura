// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura

Rectangle
{
    id: root
    property alias packageData: packageCardHeader.packageData

    height: childrenRect.height
    color: UM.Theme.getColor("main_background")
    radius: UM.Theme.getSize("default_radius").width

    Column
    {
        width: parent.width

        spacing: 0

        Item
        {
            width: parent.width
            height: UM.Theme.getSize("card").height

            PackageCardHeader
            {
                id: packageCardHeader
                showManageButtons: true

                anchors.fill: parent

                Row
                {
                    id: downloadCount
                    Layout.preferredWidth: parent.width
                    Layout.fillHeight: true
                    visible: packageData.downloadCount != "0"
                    UM.RecolorImage
                    {
                        id: downloadsIcon
                        width: UM.Theme.getSize("card_tiny_icon").width
                        height: UM.Theme.getSize("card_tiny_icon").height

                        source: UM.Theme.getIcon("Download")
                        color: UM.Theme.getColor("text")
                    }

                    Label
                    {

                        anchors.verticalCenter: downloadsIcon.verticalCenter

                        color: UM.Theme.getColor("text")
                        font: UM.Theme.getFont("default")
                        text: packageData.downloadCount
                    }
                }
            }
        }

        Column
        {
            id: extendedDescription
            width: parent.width

            padding: UM.Theme.getSize("default_margin").width
            topPadding: 0
            spacing: UM.Theme.getSize("default_margin").height

            Label
            {
                width: parent.width - parent.padding * 2

                text: catalog.i18nc("@header", "Description")
                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("text")
                elide: Text.ElideRight
            }

            Label
            {
                width: parent.width - parent.padding * 2

                text: packageData.formattedDescription
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text")
                linkColor: UM.Theme.getColor("text_link")
                wrapMode: Text.Wrap
                textFormat: Text.RichText

                onLinkActivated: UM.UrlUtil.openUrl(link, ["http", "https"])
            }

            Column //Separate column to have no spacing between compatible printers.
            {
                id: compatiblePrinterColumn
                width: parent.width - parent.padding * 2

                visible: packageData.packageType === "material"
                spacing: 0

                Label
                {
                    width: parent.width

                    text: catalog.i18nc("@header", "Compatible printers")
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")
                    elide: Text.ElideRight
                }

                Repeater
                {
                    model: packageData.compatiblePrinters

                    Label
                    {
                        width: compatiblePrinterColumn.width

                        text: modelData
                        font: UM.Theme.getFont("medium")
                        color: UM.Theme.getColor("text")
                        elide: Text.ElideRight
                    }
                }

                Label
                {
                    width: parent.width

                    visible: packageData.compatiblePrinters.length == 0
                    text: "(" + catalog.i18nc("@info", "No compatibility information") + ")"
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    elide: Text.ElideRight
                }
            }

            Column
            {
                id: compatibleSupportMaterialColumn
                width: parent.width - parent.padding * 2

                visible: packageData.packageType === "material"
                spacing: 0

                Label
                {
                    width: parent.width

                    text: catalog.i18nc("@header", "Compatible support materials")
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")
                    elide: Text.ElideRight
                }

                Repeater
                {
                    model: packageData.compatibleSupportMaterials

                    Label
                    {
                        width: compatibleSupportMaterialColumn.width

                        text: modelData
                        font: UM.Theme.getFont("medium")
                        color: UM.Theme.getColor("text")
                        elide: Text.ElideRight
                    }
                }

                Label
                {
                    width: parent.width

                    visible: packageData.compatibleSupportMaterials.length == 0
                    text: "(" + catalog.i18nc("@info No materials", "None") + ")"
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    elide: Text.ElideRight
                }
            }

            Column
            {
                width: parent.width - parent.padding * 2

                visible: packageData.packageType === "material"
                spacing: 0

                Label
                {
                    width: parent.width

                    text: catalog.i18nc("@header", "Compatible with Material Station")
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")
                    elide: Text.ElideRight
                }

                Label
                {
                    width: parent.width

                    text: packageData.isCompatibleMaterialStation ? catalog.i18nc("@info", "Yes") : catalog.i18nc("@info", "No")
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    elide: Text.ElideRight
                }
            }

            Column
            {
                width: parent.width - parent.padding * 2

                visible: packageData.packageType === "material"
                spacing: 0

                Label
                {
                    width: parent.width

                    text: catalog.i18nc("@header", "Optimized for Air Manager")
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")
                    elide: Text.ElideRight
                }

                Label
                {
                    width: parent.width

                    text: packageData.isCompatibleAirManager ? catalog.i18nc("@info", "Yes") : catalog.i18nc("@info", "No")
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    elide: Text.ElideRight
                }
            }

            Row
            {
                id: externalButtonRow
                anchors.horizontalCenter: parent.horizontalCenter

                spacing: UM.Theme.getSize("narrow_margin").width

                Cura.SecondaryButton
                {
                    text: packageData.packageType === "plugin" ? catalog.i18nc("@button", "Visit plug-in website") : catalog.i18nc("@button", "Website")
                    iconSource: UM.Theme.getIcon("Globe")
                    outlineColor: "transparent"
                    onClicked: Qt.openUrlExternally(packageData.packageInfoUrl)
                }

                Cura.SecondaryButton
                {
                    visible: packageData.packageType === "material"
                    text: catalog.i18nc("@button", "Buy spool")
                    iconSource: UM.Theme.getIcon("ShoppingCart")
                    outlineColor: "transparent"
                    onClicked: Qt.openUrlExternally(packageData.whereToBuy)
                }

                Cura.SecondaryButton
                {
                    visible: packageData.packageType === "material"
                    text: catalog.i18nc("@button", "Safety datasheet")
                    iconSource: UM.Theme.getIcon("Warning")
                    outlineColor: "transparent"
                    onClicked: Qt.openUrlExternally(packageData.safetyDataSheet)
                }

                Cura.SecondaryButton
                {
                    visible: packageData.packageType === "material"
                    text: catalog.i18nc("@button", "Technical datasheet")
                    iconSource: UM.Theme.getIcon("DocumentFilled")
                    outlineColor: "transparent"
                    onClicked: Qt.openUrlExternally(packageData.technicalDataSheet)
                }
            }
        }
    }

    FontMetrics
    {
        id: fontMetrics
        font: UM.Theme.getFont("default")
    }
}
