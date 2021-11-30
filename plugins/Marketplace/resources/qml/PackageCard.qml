// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura

Rectangle
{
    property var packageData
    property bool expanded: false

    height: childrenRect.height
    color: UM.Theme.getColor("main_background")
    radius: UM.Theme.getSize("default_radius").width

    states:
    [
        State
        {
            name: "Folded"
            when: !expanded
            PropertyChanges
            {
                target: shortDescription
                visible: true
            }
            PropertyChanges
            {
                target: downloadCount
                visible: false
            }
            PropertyChanges
            {
                target: extendedDescription
                visible: false
            }
        },
        State
        {
            name: "Expanded"
            when: expanded
            PropertyChanges
            {
                target: shortDescription
                visible: false
            }
            PropertyChanges
            {
                target: downloadCount
                visible: true
            }
            PropertyChanges
            {
                target: extendedDescription
                visible: true
            }
        }
    ]

    Column
    {
        width: parent.width

        spacing: 0

        Item
        {
            width: parent.width
            height: UM.Theme.getSize("card").height

            Image
            {
                id: packageItem
                anchors
                {
                    top: parent.top
                    left: parent.left
                    margins: UM.Theme.getSize("default_margin").width
                }
                width: UM.Theme.getSize("card_icon").width
                height: width

                source: packageData.iconUrl != "" ? packageData.iconUrl : "../images/placeholder.svg"
            }

            ColumnLayout
            {
                anchors
                {
                    left: packageItem.right
                    leftMargin: UM.Theme.getSize("default_margin").width
                    right: parent.right
                    rightMargin: UM.Theme.getSize("thick_margin").width
                    top: parent.top
                    topMargin: UM.Theme.getSize("narrow_margin").height
                }
                height: packageItem.height + packageItem.anchors.margins * 2

                // Title row.
                RowLayout
                {
                    id: titleBar
                    Layout.preferredWidth: parent.width
                    Layout.preferredHeight: childrenRect.height

                    Label
                    {
                        text: packageData.displayName
                        font: UM.Theme.getFont("medium_bold")
                        color: UM.Theme.getColor("text")
                        verticalAlignment: Text.AlignTop
                    }

                    Control
                    {
                        Layout.preferredWidth: UM.Theme.getSize("card_tiny_icon").width
                        Layout.preferredHeight: UM.Theme.getSize("card_tiny_icon").height


                        enabled: packageData.isCheckedByUltimaker
                        visible: packageData.isCheckedByUltimaker

                        Cura.ToolTip
                        {
                            tooltipText:
                            {
                                switch(packageData.packageType)
                                {
                                    case "plugin": return catalog.i18nc("@info", "Ultimaker Verified Plug-in");
                                    case "material": return catalog.i18nc("@info", "Ultimaker Certified Material");
                                    default: return catalog.i18nc("@info", "Ultimaker Verified Package");
                                }
                            }
                            visible: parent.hovered
                            targetPoint: Qt.point(0, Math.round(parent.y + parent.height / 2))
                        }

                        Rectangle
                        {
                            anchors.fill: parent
                            color: UM.Theme.getColor("action_button_hovered")
                            radius: width
                            UM.RecolorImage
                            {
                                anchors.fill: parent
                                color: UM.Theme.getColor("primary")
                                source: packageData.packageType == "plugin" ? UM.Theme.getIcon("CheckCircle") : UM.Theme.getIcon("Certified")
                            }
                        }

                        //NOTE: Can we link to something here? (Probably a static link explaining what verified is):
                        // onClicked: Qt.openUrlExternally( XXXXXX )
                    }

                    Control
                    {
                        Layout.preferredWidth: UM.Theme.getSize("card_tiny_icon").width
                        Layout.preferredHeight: UM.Theme.getSize("card_tiny_icon").height
                        Layout.alignment: Qt.AlignCenter
                        enabled: false  // remove!
                        visible: false  // replace packageInfo.XXXXXX
                        // TODO: waiting for materials card implementation

                        Cura.ToolTip
                        {
                            tooltipText: "" // TODO
                            visible: parent.hovered
                        }

                        UM.RecolorImage
                        {
                            anchors.fill: parent

                            color: UM.Theme.getColor("primary")
                            source: UM.Theme.getIcon("CheckCircle") // TODO
                        }

                        // onClicked: Qt.openUrlExternally( XXXXXX )  // TODO
                    }

                    Label
                    {
                        id: packageVersionLabel
                        text: packageData.packageVersion
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                        Layout.fillWidth: true
                    }

                    Button
                    {
                        id: externalLinkButton

                        // For some reason if i set padding, they don't match up. If i set all of them explicitly, it does work?
                        leftPadding: UM.Theme.getSize("narrow_margin").width
                        rightPadding: UM.Theme.getSize("narrow_margin").width
                        topPadding: UM.Theme.getSize("narrow_margin").width
                        bottomPadding: UM.Theme.getSize("narrow_margin").width

                        Layout.preferredWidth: UM.Theme.getSize("card_tiny_icon").width + 2 * padding
                        Layout.preferredHeight: UM.Theme.getSize("card_tiny_icon").width + 2 * padding
                        contentItem: UM.RecolorImage
                        {
                            source: UM.Theme.getIcon("LinkExternal")
                            color: UM.Theme.getColor("icon")
                            implicitWidth: UM.Theme.getSize("card_tiny_icon").width
                            implicitHeight: UM.Theme.getSize("card_tiny_icon").height
                        }

                        background: Rectangle
                        {
                            color: externalLinkButton.hovered ? UM.Theme.getColor("action_button_hovered"): "transparent"
                            radius: externalLinkButton.width / 2
                        }
                        onClicked: Qt.openUrlExternally(packageData.authorInfoUrl)
                    }
                }

                Item
                {
                    id: shortDescription
                    Layout.preferredWidth: parent.width
                    Layout.fillHeight: true

                    Label
                    {
                        id: descriptionLabel
                        width: parent.width
                        property real lastLineWidth: 0; //Store the width of the last line, to properly position the elision.

                        text: packageData.description
                        textFormat: Text.PlainText //Must be plain text, or we won't get onLineLaidOut signals. Don't auto-detect!
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                        maximumLineCount: 2
                        wrapMode: Text.Wrap
                        elide: Text.ElideRight
                        visible: text !== ""

                        onLineLaidOut:
                        {
                            if(truncated && line.isLast)
                            {
                                let max_line_width = parent.width - readMoreButton.width - fontMetrics.advanceWidth("… ") - 2 * UM.Theme.getSize("default_margin").width;
                                if(line.implicitWidth > max_line_width)
                                {
                                    line.width = max_line_width;
                                }
                                else
                                {
                                    line.width = line.implicitWidth - fontMetrics.advanceWidth("…"); //Truncate the ellipsis. We're adding this ourselves.
                                }
                                descriptionLabel.lastLineWidth = line.implicitWidth;
                            }
                        }
                    }
                    Label
                    {
                        id: tripleDotLabel
                        anchors.left: parent.left
                        anchors.leftMargin: descriptionLabel.lastLineWidth
                        anchors.bottom: descriptionLabel.bottom

                        text: "… "
                        font: descriptionLabel.font
                        color: descriptionLabel.color
                        visible: descriptionLabel.truncated && descriptionLabel.text !== ""
                    }
                    Cura.TertiaryButton
                    {
                        id: readMoreButton
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: fontMetrics.height //Height of a single line.

                        text: catalog.i18nc("@info", "Read more")
                        iconSource: UM.Theme.getIcon("LinkExternal")

                        visible: descriptionLabel.truncated && descriptionLabel.text !== ""
                        enabled: visible
                        leftPadding: UM.Theme.getSize("default_margin").width
                        rightPadding: UM.Theme.getSize("wide_margin").width
                        textFont: descriptionLabel.font
                        isIconOnRightSide: true

                        onClicked: Qt.openUrlExternally(packageData.packageInfoUrl)
                    }
                }

                Row
                {
                    id: downloadCount
                    Layout.preferredWidth: parent.width
                    Layout.fillHeight: true

                    UM.RecolorImage
                    {
                        id: downloadsIcon
                        width: UM.Theme.getSize("card_tiny_icon").width
                        height: UM.Theme.getSize("card_tiny_icon").height

                        visible: packageData.installationStatus !== "bundled" //Don't show download count for packages that are bundled. It'll usually be 0.
                        source: UM.Theme.getIcon("Download")
                        color: UM.Theme.getColor("text")
                    }

                    Label
                    {
                        anchors.verticalCenter: downloadsIcon.verticalCenter

                        visible: packageData.installationStatus !== "bundled" //Don't show download count for packages that are bundled. It'll usually be 0.
                        color: UM.Theme.getColor("text")
                        font: UM.Theme.getFont("default")
                        text: packageData.downloadCount
                    }
                }

                // Author and action buttons.
                RowLayout
                {
                    id: authorAndActionButton
                    Layout.preferredWidth: parent.width
                    Layout.preferredHeight: childrenRect.height

                    spacing: UM.Theme.getSize("narrow_margin").width

                    Label
                    {
                        id: authorBy
                        Layout.alignment: Qt.AlignTop

                        text: catalog.i18nc("@label", "By")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                    }

                    Cura.TertiaryButton
                    {
                        Layout.fillWidth: true
                        Layout.preferredHeight: authorBy.height
                        Layout.alignment: Qt.AlignTop

                        text: packageData.authorName
                        textFont: UM.Theme.getFont("default_bold")
                        textColor: UM.Theme.getColor("text") // override normal link color
                        leftPadding: 0
                        rightPadding: 0
                        iconSource: UM.Theme.getIcon("LinkExternal")
                        isIconOnRightSide: true

                        onClicked: Qt.openUrlExternally(packageData.authorInfoUrl)
                    }

                    Cura.SecondaryButton
                    {
                        id: disableButton
                        Layout.alignment: Qt.AlignTop
                        text: catalog.i18nc("@button", "Disable")
                        visible: false  // not functional right now, also only when unfolding and required
                    }

                    Cura.SecondaryButton
                    {
                        id: uninstallButton
                        Layout.alignment: Qt.AlignTop
                        text: catalog.i18nc("@button", "Uninstall")
                        visible: false  // not functional right now, also only when unfolding and required
                    }

                    Cura.PrimaryButton
                    {
                        id: installButton
                        Layout.alignment: Qt.AlignTop
                        text: catalog.i18nc("@button", "Update") // OR Download, if new!
                        visible: false  // not functional right now, also only when unfolding and required
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

            Cura.SecondaryButton
            {
                anchors.horizontalCenter: parent.horizontalCenter

                text: catalog.i18nc("@button", "Visit plug-in website")
                iconSource: UM.Theme.getIcon("Globe")
                outlineColor: "transparent"
                onClicked: Qt.openUrlExternally(packageData.packageInfoUrl)
            }
        }
    }

    FontMetrics
    {
        id: fontMetrics
        font: UM.Theme.getFont("default")
    }
}
