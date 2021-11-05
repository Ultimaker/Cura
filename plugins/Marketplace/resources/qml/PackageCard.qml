// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15

import UM 1.6 as UM
import Cura 1.6 as Cura

Rectangle
{
    property var packageData

    width: parent.width
    height: UM.Theme.getSize("card").height

    color: UM.Theme.getColor("main_background")
    radius: UM.Theme.getSize("default_radius").width

    Image
    {
        id: packageIcon
        anchors
        {
            top: parent.top
            left: parent.left
            margins: UM.Theme.getSize("thin_margin").width
        }
        width: UM.Theme.getSize("section_icon").width * 3
        height: UM.Theme.getSize("section_icon").height * 3

        source: packageData.iconUrl != "" ? packageData.iconUrl : UM.Theme.getImage("CicleOutline")
    }

    Item
    {
        anchors
        {
            top: parent.top
            bottom: parent.bottom
            right: parent.right
            left: packageIcon.left
            margins: UM.Theme.getSize("thin_margin").width
        }

        Item
        {
            id: firstRowItems
            anchors
            {
                top: parent.top
                right: parent.right
                left: parent.left
                margins: UM.Theme.getSize("thin_margin").width
            }

            Label
            {
                id: titleLabel
                anchors
                {
                    top: parent.top
                    left: parent.left
                    margins: UM.Theme.getSize("thin_margin").width
                }
                font: UM.Theme.getFont("medium_bold")
                color: UM.Theme.getColor("text")

                text: packageData.displayName
            }

            UM.RecolorImage
            {
                id: verifiedIcon
                anchors
                {
                    top: parent.top
                    left: titleLabel.right
                    margins: UM.Theme.getSize("thin_margin").width
                }
                width: UM.Theme.getSize("section_icon").height
                height: UM.Theme.getSize("section_icon").height
                color: UM.Theme.getColor("icon")

                visible: packageData.isVerified
                source: UM.Theme.getIcon("CheckCircle")

                // TODO: on hover
            }

            Rectangle
            {   // placeholder for 'certified material' icon+link whenever we implement the materials part of this card
                id: certifiedIcon
                anchors
                {
                    top: parent.top
                    left: verifiedIcon.right
                    margins: UM.Theme.getSize("thin_margin").width
                }
                width: UM.Theme.getSize("section_icon").height
                height: UM.Theme.getSize("section_icon").height

                // TODO: on hover
            }

            Label
            {
                id: versionLabel
                anchors
                {
                    top: parent.top
                    left: certifiedIcon.right
                    margins: UM.Theme.getSize("thin_margin").width
                }

                text: packageData.packageVersion
            }

            UM.RecolorImage
            {
                id: packageInfoLink
                anchors
                {
                    top: parent.top
                    right: parent.right
                    margins: UM.Theme.getSize("thin_margin").width
                }
                width: UM.Theme.getSize("section_icon").height
                height: UM.Theme.getSize("section_icon").height
                color: UM.Theme.getColor("icon")

                source: UM.Theme.getIcon("Link")

                // TODO: on clicked url
            }
        }

        Item
        {
            id: secondRowItems
            anchors
            {
                top: firstRowItems.bottom
                right: parent.right
                left: parent.left
                margins: UM.Theme.getSize("thin_margin").width
            }

            UM.RecolorImage
            {
                id: downloadCountIcon
                anchors
                {
                    top: parent.top
                    left: parent.left
                    margins: UM.Theme.getSize("thin_margin").width
                }
                width: UM.Theme.getSize("section_icon").height
                height: UM.Theme.getSize("section_icon").height
                color: UM.Theme.getColor("icon")

                source: UM.Theme.getIcon("Download") // TODO: The right icon.
            }

            Label
            {
                id: downloadCountLobel
                anchors
                {
                    top: parent.top
                    left: downloadCountIcon.right
                    margins: UM.Theme.getSize("thin_margin").width
                }

                text: packageData.downloadCount
            }
        }

        Item
        {
            id: mainRowItems
            anchors
            {
                top: secondRowItems.bottom
                bottom: footerRowItems.top
                right: parent.right
                left: parent.left
                margins: UM.Theme.getSize("thin_margin").width
            }

            readonly property int charLimitSmall: 130

            Label
            {
                id: descriptionLabel
                anchors
                {
                    top: parent.top
                    left: parent.left
                    right: parent.right
                    bottom: parent.bottom
                    margins: UM.Theme.getSize("thin_margin").width
                }

                maximumLineCount: 2
                text: packageData.description.substring(0, parent.charLimitSmall)
            }

            Cura.TertiaryButton
            {
                id: readMoreLabel
                anchors
                {
                    right: parent.right
                    bottom: parent.bottom
                    margins: UM.Theme.getSize("thin_margin").width
                }

                visible: descriptionLabel.text.length > parent.charLimitSmall
                text: catalog.i18nc("@info", "Read more")

                // TODO: overlaps elided text, is this ok?
            }

            // TODO: _only_ limit to 130 or 2 rows (& all that that entails) when 'small'
        }

        Item
        {
            id: footerRowItems
            anchors
            {
                bottom: parent.bottom
                right: parent.right
                left: parent.left
                margins: UM.Theme.getSize("thin_margin").width
            }

            Item
            {
                Label
                {
                    id: preAuthorNameText
                    anchors
                    {
                        top: parent.top
                        left: parent.left
                        margins: UM.Theme.getSize("thin_margin").width
                    }

                    text: catalog.i18nc("@label", "By")
                }

                Cura.TertiaryButton
                {
                    id: authorNameLabel
                    anchors
                    {
                        top: parent.top
                        left: preAuthorNameText.right
                        margins: UM.Theme.getSize("thin_margin").width
                    }

                    text: packageData.authorName

                    // TODO on clicked (is link) -> MouseArea?
                }
            }

            Item
            {
                id: packageActionButtons
                anchors
                {
                    bottom: parent.bottom
                    right: parent.right
                    margins: UM.Theme.getSize("thin_margin").width
                }

                Cura.SecondaryButton
                {
                    id: disableButton
                    anchors
                    {
                        right: uninstallButton.left
                        bottom: parent.bottom
                        margins: UM.Theme.getSize("thin_margin").width
                    }
                    height: parent.height

                    text: catalog.i18nc("@button", "Disable")
                    // not functional right now
                }

                Cura.SecondaryButton
                {
                    id: uninstallButton
                    anchors
                    {
                        right: updateButton.left
                        bottom: parent.bottom
                        margins: UM.Theme.getSize("thin_margin").width
                    }
                    height: parent.height

                    text: catalog.i18nc("@button", "Uninstall")
                    // not functional right now
                }

                Cura.PrimaryButton
                {
                    id: updateButton
                    anchors
                    {
                        right: parent.right
                        bottom: parent.bottom
                        margins: UM.Theme.getSize("thin_margin").width
                    }
                    height: parent.height

                    text: catalog.i18nc("@button", "Update")
                    // not functional right now
                }
            }
        }
    }
}
