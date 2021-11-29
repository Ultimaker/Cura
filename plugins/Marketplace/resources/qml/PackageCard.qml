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
                            targetPoint: Qt.point(0, Math.round(parent.y + parent.height / 4))
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

                    ManageButton
                    {
                        id: enableManageButton
                        Layout.alignment: Qt.AlignTop
                        primaryText: catalog.i18nc("@button", "Enable")
                        busyPrimaryText: catalog.i18nc("@button", "enabling...")
                        secondaryText: catalog.i18nc("@button", "Disable")
                        busySecondaryText: catalog.i18nc("@button", "disabling...")
                        mainState: packageData.manageEnableState
                        enabled: !(installManageButton.busy || updateManageButton.busy)
                    }
                    Connections
                    {
                        target: enableManageButton
                        function onClicked(primary_action)
                        {
                            if (primary_action)
                            {
                                packageData.enablePackageTriggered(packageData.packageId)
                            }
                            else
                            {
                                packageData.disablePackageTriggered(packageData.packageId)
                            }
                        }
                    }

                    ManageButton
                    {
                        id: installManageButton
                        Layout.alignment: Qt.AlignTop
                        primaryText: catalog.i18nc("@button", "Install")
                        busyPrimaryText: catalog.i18nc("@button", "installing...")
                        secondaryText: catalog.i18nc("@button", "Uninstall")
                        busySecondaryText: catalog.i18nc("@button", "uninstalling...")
                        mainState: packageData.manageInstallState
                        busy: packageData.isInstalling
                        enabled: !(enableManageButton.busy || updateManageButton.busy)
                    }
                    Connections
                    {
                        target: installManageButton
                        function onClicked(primary_action)
                        {
                            packageData.isInstalling = true
                            if (primary_action)
                            {
                                packageData.installPackageTriggered(packageData.packageId)
                            }
                            else
                            {
                                packageData.uninstallPackageTriggered(packageData.packageId)
                            }
                        }
                    }

                    ManageButton
                    {
                        id: updateManageButton
                        Layout.alignment: Qt.AlignTop
                        primaryText: catalog.i18nc("@button", "Update")
                        busyPrimaryText: catalog.i18nc("@button", "updating...")
                        mainState: packageData.manageUpdateState
                        busy: packageData.isUpdating
                        enabled: !(installManageButton.busy || enableManageButton.busy)
                    }
                    Connections
                    {
                        target: updateManageButton
                        function onClicked(primary_action)
                        {
                            packageData.isUpdating = true
                            packageData.updatePackageTriggered(packageData.packageId)
                        }
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
