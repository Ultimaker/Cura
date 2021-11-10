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
    height: childrenRect.height

    color: UM.Theme.getColor("main_background")
    radius: UM.Theme.getSize("default_radius").width

    RowLayout
    {
        width: parent.width - UM.Theme.getSize("thin_margin").width * 2
        x: UM.Theme.getSize("thin_margin").width
        y: UM.Theme.getSize("thin_margin").height

        spacing: UM.Theme.getSize("thin_margin").width

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

            RowLayout //Title row.
            {
                Layout.alignment: Qt.AlignTop
                width: parent.width

                Label
                {
                    Layout.alignment: Qt.AlignTop

                    text: packageData.displayName
                    font: UM.Theme.getFont("medium_bold")
                    color: UM.Theme.getColor("text")
                }

                Row //Row inside row, but the non-layout version skips invisible elements.
                {
                    spacing: parent.spacing
                    Layout.alignment: Qt.AlignTop

                    Control
                    {
                        width: UM.Theme.getSize("card_tiny_icon").width
                        height: UM.Theme.getSize("card_tiny_icon").height
                        Layout.alignment: Qt.AlignTop

                        enabled: packageData.isVerified

                        Cura.ToolTip
                        {
                            tooltipText: catalog.i18nc("@info", "Verified")
                            visible: parent.hovered
                        }

                        UM.RecolorImage
                        {
                            anchors.fill: parent

                            color: UM.Theme.getColor("primary")
                            visible: packageData.isVerified
                            source: UM.Theme.getIcon("CheckCircle")
                        }

                        //NOTE: Can we link to something here? (Probably a static link explaining what verified is):
                        // onClicked: Qt.openUrlExternally( XXXXXX )
                    }

                    Control
                    {
                        width: UM.Theme.getSize("card_tiny_icon").width
                        height: UM.Theme.getSize("card_tiny_icon").height
                        Layout.alignment: Qt.AlignTop

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
                            visible: packageData.isVerified
                            source: UM.Theme.getIcon("CheckCircle") // TODO
                        }

                        // onClicked: Qt.openUrlExternally( XXXXXX )  // TODO
                    }
                }

                Label
                {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop

                    text: packageData.packageVersion
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                }

                Button
                {
                    Layout.preferredWidth: UM.Theme.getSize("card_tiny_icon").width
                    Layout.preferredHeight: UM.Theme.getSize("card_tiny_icon").height
                    Layout.alignment: Qt.AlignTop

                    UM.RecolorImage
                    {
                        anchors.fill: parent
                        color: UM.Theme.getColor("icon")
                        source: UM.Theme.getIcon("LinkExternal")
                    }

                    onClicked: Qt.openUrlExternally(packageData.packageInfoUrl)
                }
            }

            RowLayout
            {
                width: parent.width - UM.Theme.getSize("thin_margin").width * 2
                height: childrenRect.height
                x: UM.Theme.getSize("thin_margin").width
                y: UM.Theme.getSize("thin_margin").height

                spacing: UM.Theme.getSize("thin_margin").width

                enabled: false  // remove
                visible: false  // replace w state?
                // TODO: hide/unhide on states (folded versus header state)

                UM.RecolorImage
                {
                    id: downloadCountIcon
                    width: UM.Theme.getSize("card_tiny_icon").height
                    height: UM.Theme.getSize("card_tiny_icon").height
                    color: UM.Theme.getColor("icon")

                    source: UM.Theme.getIcon("Download")
                }

                Label
                {
                    id: downloadCountLabel
                    anchors.left: downloadCountIcon.right

                    text: packageData.downloadCount
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
                    font: UM.Theme.getFont("medium")
                    color: UM.Theme.getColor("text")
                    maximumLineCount: 2
                    wrapMode: Text.Wrap
                    elide: Text.ElideRight

                    onLineLaidOut:
                    {
                        if(truncated && line.isLast)
                        {
                            let max_line_width = parent.width - readMoreButton.width - fontMetrics.advanceWidth("… ") - UM.Theme.getSize("default_margin").width;
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

                    // NOTE: Is this the right URL for this action?
                    onClicked: Qt.openUrlExternally(packageData.packageInfoUrl)
                }

                Label
                {
                    anchors.left: parent.left
                    anchors.leftMargin: descriptionLabel.lastLineWidth
                    anchors.bottom: readMoreButton.bottom

                    text: "… "
                    font: descriptionLabel.font
                    color: descriptionLabel.color
                    visible: descriptionLabel.truncated
                }
            }

            RowLayout //Author and action buttons.
            {
                width: parent.width
                Layout.alignment: Qt.AlignBottom
                spacing: UM.Theme.getSize("thin_margin").width

                Label
                {
                    id: authorBy
                    Layout.alignment: Qt.AlignBottom

                    text: catalog.i18nc("@label", "By")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                }

                Cura.TertiaryButton
                {
                    Layout.fillWidth: true
                    Layout.preferredHeight: authorBy.height
                    Layout.alignment: Qt.AlignBottom

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
                    Layout.alignment: Qt.AlignBottom
                    Layout.preferredHeight: authorBy.height
                    text: catalog.i18nc("@button", "Disable")
                    // not functional right now
                }

                Cura.SecondaryButton
                {
                    Layout.alignment: Qt.AlignBottom
                    Layout.preferredHeight: authorBy.height
                    text: catalog.i18nc("@button", "Uninstall")
                    // not functional right now
                }

                Cura.PrimaryButton
                {
                    Layout.alignment: Qt.AlignBottom
                    Layout.preferredHeight: authorBy.height
                    text: catalog.i18nc("@button", "Update")
                    // not functional right now
                }
            }
        }
    }

    FontMetrics
    {
        id: fontMetrics
        font: UM.Theme.getFont("medium")
    }
}
