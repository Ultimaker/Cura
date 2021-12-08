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

            // card icon
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

            //
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

                // description
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
                        anchors.bottom: descriptionLabel.bottom
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

                // Author and action buttons.
                RowLayout
                {
                    id: authorAndActionButton
                    Layout.preferredWidth: parent.width
                    Layout.preferredHeight: childrenRect.height

                    spacing: UM.Theme.getSize("narrow_margin").width

                    // label "By"
                    Label
                    {
                        id: authorBy
                        Layout.alignment: Qt.AlignCenter

                        text: catalog.i18nc("@label", "By")
                        font: UM.Theme.getFont("default")
                        color: UM.Theme.getColor("text")
                    }

                    // clickable author name
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
                        visible: (root.manageableInListView || installManageButton.confirmed) && !(enableManageButton.confirmed || updateManageButton.confirmed)
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
                        visible: (root.manageableInListView) && (!installManageButton.confirmed || updateManageButton.confirmed)

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
    }

    FontMetrics
    {
        id: fontMetrics
        font: UM.Theme.getFont("default")
    }
}
