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
    property var packageData
    property bool manageableInListView

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
                    rightMargin: UM.Theme.getSize("default_margin").width
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
                    VerifiedIcon
                    {
                        enabled: packageData.isCheckedByUltimaker
                        visible: packageData.isCheckedByUltimaker
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
                        Layout.alignment: Qt.AlignCenter

                        text: catalog.i18nc("@label", "By")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                    }

                    Cura.TertiaryButton
                    {
                        Layout.fillWidth: true
                        Layout.preferredHeight: authorBy.height
                        Layout.alignment: Qt.AlignCenter

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
                        visible: !(installManageButton.confirmed || updateManageButton.confirmed) || enableManageButton.confirmed
                        button_style: packageData.stateManageEnableButton
                        Layout.alignment: Qt.AlignTop
                        busy: packageData.enableManageButton == "busy"
                        confirmed: packageData.enableManageButton == "confirmed"
                        text: {
                            switch (packageData.stateManageEnableButton) {
                                case "primary":
                                    return catalog.i18nc("@button", "Enable");
                                case "secondary":
                                    return catalog.i18nc("@button", "Disable");
                                case "busy":
                                    if (packageData.installationStatus) {
                                        return catalog.i18nc("@button", "Enabling...");
                                    } else {
                                        return catalog.i18nc("@button", "Disabling...");
                                    }
                                case "confirmed":
                                    if (packageData.installationStatus) {
                                        return catalog.i18nc("@button", "Enabled");
                                    } else {
                                        return catalog.i18nc("@button", "Disabled");
                                    }
                                default:
                                    return "";
                            }
                        }
                        enabled: !installManageButton.busy && !updateManageButton.busy

                        onClicked:
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
                        visible: !(enableManageButton.confirmed || updateManageButton.confirmed)
                        button_style: packageData.stateManageInstallButton
                        busy: packageData.stateManageInstallButton == "busy"
                        confirmed: packageData.stateManageInstallButton == "confirmed"
                        Layout.alignment: Qt.AlignTop
                        text: {
                            switch (packageData.stateManageInstallButton) {
                                case "primary":
                                    return catalog.i18nc("@button", "Install");
                                case "secondary":
                                    return catalog.i18nc("@button", "Uninstall");
                                case "busy":
                                    if (packageData.installationStatus) {
                                        return catalog.i18nc("@button", "Installing...");
                                    } else {
                                        return catalog.i18nc("@button", "Uninstalling...");
                                    }
                                case "confirmed":
                                    if (packageData.installationStatus) {
                                        return catalog.i18nc("@button", "Installed");
                                    } else {
                                        return catalog.i18nc("@button", "Uninstalled");
                                    }
                                default:
                                    return "";
                            }
                        }
                        enabled: !enableManageButton.busy && !updateManageButton.busy

                        onClicked:
                        {
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
                        visible: !installManageButton.confirmed || updateManageButton.confirmed

                        button_style: packageData.stateManageUpdateButton
                        busy: packageData.stateManageUpdateButton == "busy"
                        confirmed: packageData.stateManageUpdateButton == "confirmed"
                        Layout.alignment: Qt.AlignTop
                        enabled: !installManageButton.busy && !enableManageButton.busy

                        text: {
                            switch (packageData.stateManageInstallButton) {
                                case "primary":
                                    return catalog.i18nc("@button", "Update");
                                case "busy":
                                    return catalog.i18nc("@button", "Updating...");
                                case "confirmed":
                                    return catalog.i18nc("@button", "Updated");
                                default:
                                    return "";
                            }
                        }

                        onClicked: packageData.updatePackageTriggered(packageData.packageId)
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
