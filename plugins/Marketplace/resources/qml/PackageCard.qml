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

    height: UM.Theme.getSize("card").height
    color: UM.Theme.getColor("main_background")
    radius: UM.Theme.getSize("default_radius").width

    states:
    [
        State
        {
            name: "Folded"
            when: true  // TODO
            PropertyChanges
            {
                target: descriptionArea
                visible: true
            }
        },
        State
        {
            name: "Header"
            when: false  // TODO
            PropertyChanges
            {
                target: descriptionArea
                visible: false
            }
        }
    ]

    // Separate column for icon on the left.
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

    // Title row.
    RowLayout
    {
        id: titleBar
        anchors
        {
            left: packageItem.right
            right: parent.right
            top: parent.top
            topMargin: UM.Theme.getSize("narrow_margin").height
            leftMargin: UM.Theme.getSize("default_margin").width
            rightMargin:UM.Theme.getSize("thick_margin").width
        }

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
        id: descriptionArea
        height: descriptionLabel.height
        anchors
        {
            top: titleBar.bottom
            left: packageItem.right
            right: parent.right
            rightMargin: UM.Theme.getSize("default_margin").width
            leftMargin: UM.Theme.getSize("default_margin").width
        }
        Label
        {
            id: descriptionLabel
            width: parent.width
            property real lastLineWidth: 0; //Store the width of the last line, to properly position the elision.

            text: packageData.description
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            maximumLineCount: 2
            wrapMode: Text.Wrap
            elide: Text.ElideRight

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
            anchors.bottom: readMoreButton.bottom

            text: "… "
            font: descriptionLabel.font
            color: descriptionLabel.color
            visible: descriptionLabel.truncated
        }
        Cura.TertiaryButton
        {
            id: readMoreButton
            anchors.left: tripleDotLabel.right
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

            onClicked: Qt.openUrlExternally(packageData.packageInfoUrl)
        }
    }

    // Author and action buttons.
    RowLayout
    {
        id: authorAndActionButton
        width: parent.width
        anchors
        {
            bottom: parent.bottom
            left: packageItem.right
            margins: UM.Theme.getSize("default_margin").height
        }
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

    FontMetrics
    {
        id: fontMetrics
        font: UM.Theme.getFont("default")
    }
}
