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

    width: parent ? parent.width : 0
    height: childrenRect.height + UM.Theme.getSize("default_margin").height * 2

    color: UM.Theme.getColor("main_background")
    radius: UM.Theme.getSize("default_radius").width

    RowLayout
    {
        width: parent.width - UM.Theme.getSize("default_margin").width * 2
        height: childrenRect.height
        x: UM.Theme.getSize("default_margin").width
        y: UM.Theme.getSize("default_margin").height

        spacing: UM.Theme.getSize("default_margin").width

        Image //Separate column for icon on the left.
        {
            Layout.preferredWidth: UM.Theme.getSize("card_icon").width
            Layout.preferredHeight: UM.Theme.getSize("card_icon").height
            Layout.alignment: Qt.AlignTop

            source: packageData.iconUrl != "" ? packageData.iconUrl : "../images/placeholder.svg"
        }

        Column
        {
            Layout.fillWidth: true
            Layout.preferredHeight: childrenRect.height
            Layout.alignment: Qt.AlignTop

            spacing: UM.Theme.getSize("default_margin").height

            RowLayout //Title row.
            {
                width: parent.width

                spacing: UM.Theme.getSize("default_margin").width

                Label
                {
                    Layout.alignment: Qt.AlignTop

                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")

                    text: packageData.displayName
                }

                UM.RecolorImage
                {
                    Layout.preferredWidth: visible ? UM.Theme.getSize("section_icon").width : 0
                    Layout.preferredHeight: visible ? UM.Theme.getSize("section_icon").height : 0
                    Layout.alignment: Qt.AlignTop

                    color: UM.Theme.getColor("icon")
                    visible: packageData.isVerified
                    source: UM.Theme.getIcon("CheckCircle")

                    // TODO: on hover
                }

                Rectangle
                {   // placeholder for 'certified material' icon+link whenever we implement the materials part of this card
                    Layout.preferredWidth: visible ? UM.Theme.getSize("section_icon").width : 0
                    Layout.preferredHeight: visible ? UM.Theme.getSize("section_icon").height : 0
                    Layout.alignment: Qt.AlignTop

                    // TODO: on hover
                }

                Label
                {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop

                    text: packageData.packageVersion
                }

                UM.RecolorImage
                {
                    Layout.preferredWidth: UM.Theme.getSize("section_icon").width
                    Layout.preferredHeight: UM.Theme.getSize("section_icon").height
                    Layout.alignment: Qt.AlignTop

                    color: UM.Theme.getColor("icon")
                    source: UM.Theme.getIcon("Link")

                    // TODO: on clicked url
                }
            }

            Item
            {
                width: parent.width
                height: descriptionLabel.height

                Label
                {
                    id: descriptionLabel
                    width: parent.width
                    property real lastLineWidth: 0; //Store the width of the last line, to properly position the elision.

                    text: packageData.description
                    maximumLineCount: 2
                    wrapMode: Text.Wrap
                    elide: Text.ElideRight

                    onLineLaidOut:
                    {
                        if(truncated && line.isLast)
                        {
                            let max_line_width = parent.width - readMoreButton.width - fontMetrics.advanceWidth("… ");
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

                Cura.TertiaryButton
                {
                    id: readMoreButton
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: fontMetrics.height //Height of a single line.

                    text: catalog.i18nc("@info", "Read more")
                    iconSource: UM.Theme.getIcon("LinkExternal")

                    visible: descriptionLabel.truncated
                    enabled: visible
                    leftPadding: UM.Theme.getSize("default_margin").width
                    rightPadding: UM.Theme.getSize("wide_margin").width
                    textFont: descriptionLabel.font
                    isIconOnRightSide: true
                }

                Label
                {
                    text: "… "
                    visible: descriptionLabel.truncated
                    anchors.left: parent.left
                    anchors.leftMargin: descriptionLabel.lastLineWidth
                    anchors.bottom: readMoreButton.bottom
                }
            }

            RowLayout //Author and action buttons.
            {
                width: parent.width

                Label
                {
                    id: authorBy
                    Layout.alignment: Qt.AlignTop

                    text: catalog.i18nc("@label", "By")
                }

                Cura.TertiaryButton
                {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop

                    text: packageData.authorName

                    // TODO on clicked (is link) -> MouseArea?
                }

                Cura.SecondaryButton
                {
                    text: catalog.i18nc("@button", "Disable")
                    // not functional right now
                }

                Cura.SecondaryButton
                {
                    text: catalog.i18nc("@button", "Uninstall")
                    // not functional right now
                }

                Cura.PrimaryButton
                {
                    text: catalog.i18nc("@button", "Update")
                    // not functional right now
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
