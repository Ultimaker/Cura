// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura

// As both the PackageCard and Package contain similar components; a package icon, title, author bar. These components
// are combined into the reusable "PackageCardHeader" component
Item
{
    default property alias contents: contentItem.children

    property var packageData
    property bool showDisableButton: false
    property bool showInstallButton: false
    property bool showUpdateButton: false

    property string missingPackageReadMoreUrl: "https://support.ultimaker.com/hc/en-us/articles/360011968360-Using-the-Ultimaker-Marketplace?utm_source=cura&utm_medium=software&utm_campaign=load-file-material-missing"


    width: parent.width
    height: UM.Theme.getSize("card").height

    // card icon
    Item
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

        property bool packageHasIcon: packageData.iconUrl != ""

        Image
        {
            visible: parent.packageHasIcon
            anchors.fill: parent
            source: packageData.iconUrl
        }

        UM.ColorImage
        {
            visible: !parent.packageHasIcon
            anchors.fill: parent
            color: UM.Theme.getColor("text")
            source:
            {
                switch (packageData.packageType)
                {
                    case "plugin":
                        return Qt.resolvedUrl("../images/Plugin.svg");
                    case "material":
                        return Qt.resolvedUrl("../images/Spool.svg");
                    default:
                        return Qt.resolvedUrl("../images/placeholder.svg");
                }
            }
        }
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

            UM.StatusIcon
            {
                width: UM.Theme.getSize("section_icon").width + UM.Theme.getSize("narrow_margin").width
                height: UM.Theme.getSize("section_icon").height
                status: UM.StatusIcon.Status.WARNING
                visible: packageData.isMissingPackageInformation
            }

            UM.Label
            {
                text: packageData.displayName
                font: UM.Theme.getFont("medium_bold")
                verticalAlignment: Text.AlignTop
            }
            VerifiedIcon
            {
                enabled: packageData.isCheckedByUltimaker
                visible: packageData.isCheckedByUltimaker
            }

            UM.Label
            {
                id: packageVersionLabel
                text: packageData.packageVersion
                Layout.fillWidth: true
            }

            Button
            {
                id: externalLinkButton
                visible: !packageData.isMissingPackageInformation

                // For some reason if i set padding, they don't match up. If i set all of them explicitly, it does work?
                leftPadding: UM.Theme.getSize("narrow_margin").width
                rightPadding: UM.Theme.getSize("narrow_margin").width
                topPadding: UM.Theme.getSize("narrow_margin").width
                bottomPadding: UM.Theme.getSize("narrow_margin").width

                width: UM.Theme.getSize("card_tiny_icon").width + 2 * padding
                height: UM.Theme.getSize("card_tiny_icon").width + 2 * padding
                contentItem: UM.ColorImage
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
                onClicked: Qt.openUrlExternally(packageData.marketplaceURL)
            }
        }

        // When a package Card companent is created and children are provided to it they are rendered here
        Item {
            id: contentItem
            Layout.fillHeight: true
            Layout.preferredWidth: parent.width
        }

        // Author and action buttons.
        RowLayout
        {
            id: authorAndActionButton
            Layout.preferredWidth: parent.width
            Layout.preferredHeight: childrenRect.height

            spacing: UM.Theme.getSize("narrow_margin").width

            // label "By"
            UM.Label
            {
                id: authorBy
                visible: !packageData.isMissingPackageInformation
                Layout.alignment: Qt.AlignCenter

                text: catalog.i18nc("@label Is followed by the name of an author", "By")
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
            }

            // clickable author name
            Item
            {
                visible: !packageData.isMissingPackageInformation
                Layout.fillWidth: true
                implicitHeight: authorBy.height
                Layout.alignment: Qt.AlignTop
                Cura.TertiaryButton
                {
                    text: packageData.authorName
                    textFont: UM.Theme.getFont("default_bold")
                    textColor: UM.Theme.getColor("text") // override normal link color
                    leftPadding: 0
                    rightPadding: 0
                    iconSource: UM.Theme.getIcon("LinkExternal")
                    isIconOnRightSide: true

                    onClicked: Qt.openUrlExternally(packageData.authorInfoUrl)
                }
            }

            Item
            {
                visible: packageData.isMissingPackageInformation
                Layout.fillWidth: true
                implicitHeight: readMoreButton.height
                Layout.alignment: Qt.AlignTop
                Cura.TertiaryButton
                {
                    id: readMoreButton
                    text: catalog.i18nc("@button:label", "Learn More")
                    leftPadding: 0
                    rightPadding: 0
                    iconSource: UM.Theme.getIcon("LinkExternal")
                    isIconOnRightSide: true

                    onClicked: Qt.openUrlExternally(missingPackageReadMoreUrl)
                }
            }

            ManageButton
            {
                id: enableManageButton
                visible: showDisableButton && packageData.isInstalled && !packageData.isToBeInstalled && packageData.packageType != "material" && !packageData.isMissingPackageInformation
                enabled: !packageData.busy

                button_style: !packageData.isActive
                Layout.alignment: Qt.AlignTop

                text: button_style ? catalog.i18nc("@button", "Enable") : catalog.i18nc("@button", "Disable")

                onClicked: packageData.isActive ? packageData.disable(): packageData.enable()
            }

            ManageButton
            {
                id: installManageButton
                visible: showInstallButton && (packageData.canDowngrade || !packageData.isBundled) && !packageData.isMissingPackageInformation
                enabled: !packageData.busy
                busy: packageData.busy
                button_style: !(packageData.isInstalled || packageData.isToBeInstalled)
                Layout.alignment: Qt.AlignTop

                text:
                {
                    if (packageData.canDowngrade)
                    {
                        if (busy) { return catalog.i18nc("@button", "Downgrading..."); }
                        else { return catalog.i18nc("@button", "Downgrade"); }
                    }
                    if (!(packageData.isInstalled || packageData.isToBeInstalled))
                    {
                        if (busy) { return catalog.i18nc("@button", "Installing..."); }
                        else { return catalog.i18nc("@button", "Install"); }
                    }
                    else
                    {
                        return catalog.i18nc("@button", "Uninstall");
                    }
                }

                onClicked: packageData.isInstalled || packageData.isToBeInstalled ? packageData.uninstall(): packageData.install()
            }

            ManageButton
            {
                id: updateManageButton
                visible: showUpdateButton && packageData.canUpdate && !packageData.isMissingPackageInformation
                enabled: !packageData.busy
                busy: packageData.busy
                Layout.alignment: Qt.AlignTop

                text: busy ? catalog.i18nc("@button", "Updating..."): catalog.i18nc("@button", "Update")

                onClicked: packageData.update()
            }
        }
    }
}
