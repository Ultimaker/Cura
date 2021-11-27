// Copyright (c) 2021 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.1

import UM 1.6 as UM
import Cura 1.6 as Cura

// Onboarding banner.
Rectangle
{
    property bool bannerVisible
    property string bannerIcon
    property string bannerBody
    property var onRemoveBanner
    property string readMoreUrl

    visible: bannerVisible

    Layout.preferredHeight: childrenRect.height + 2 * UM.Theme.getSize("default_margin").height
    anchors
    {
        margins: UM.Theme.getSize("default_margin").width
        left: parent.left
        right: parent.right
        top: parent.top
    }

    color: UM.Theme.getColor("action_panel_secondary")

    // Icon
    Rectangle
    {
        id: onboardingIcon
        anchors
        {
            top: parent.top
            left: parent.left
            margins: UM.Theme.getSize("default_margin").width
        }
        width: UM.Theme.getSize("button_icon").width
        height: UM.Theme.getSize("button_icon").height
        color: "transparent"
        UM.RecolorImage
        {
            anchors.fill: parent
            color: UM.Theme.getColor("primary_text")
            source: UM.Theme.getIcon(bannerIcon)
        }
    }

    // Close button
    UM.SimpleButton
    {
        id: onboardingClose
        anchors
        {
            top: parent.top
            right: parent.right
            margins: UM.Theme.getSize("default_margin").width
        }
        width: UM.Theme.getSize("message_close").width
        height: UM.Theme.getSize("message_close").height
        color: UM.Theme.getColor("primary_text")
        hoverColor: UM.Theme.getColor("primary_text_hover")
        iconSource: UM.Theme.getIcon("Cancel")

        onClicked: onRemoveBanner()
    }

    // Body
    Label {
        id: infoText
        anchors
        {
            top: parent.top
            left: onboardingIcon.right
            right: onboardingClose.left
            margins: UM.Theme.getSize("default_margin").width
        }

        font: UM.Theme.getFont("default")
        text: bannerBody

        renderType: Text.NativeRendering
        color: "white"
        wrapMode: Text.Wrap
        elide: Text.ElideRight

        onLineLaidOut:
        {
            if(line.isLast)
            {
                // Check if read more button still fits after the body text
                if (line.implicitWidth + readMoreButton.width + UM.Theme.getSize("default_margin").width > width)
                {
                    // If it does place it after the body text
                    readMoreButton.anchors.left = infoText.left;
                    readMoreButton.anchors.bottom = infoText.bottom;
                    readMoreButton.anchors.bottomMargin = -(fontMetrics.height + UM.Theme.getSize("thin_margin").height);
                    readMoreButton.anchors.leftMargin = 0;
                }
                else
                {
                    // Otherwise place it under the text
                    readMoreButton.anchors.left = infoText.left;
                    readMoreButton.anchors.bottom = infoText.bottom;
                    readMoreButton.anchors.leftMargin = line.implicitWidth + UM.Theme.getSize("default_margin").width;
                    readMoreButton.anchors.bottomMargin = 0;
                }
            }
        }
    }

    FontMetrics
    {
        id: fontMetrics
        font: UM.Theme.getFont("default")
    }

    Cura.TertiaryButton
    {
        visible: readMoreUrl !== ""
        id: readMoreButton
        text: "Learn More"
        textFont: UM.Theme.getFont("default")
        textColor: infoText.color
        leftPadding: 0
        rightPadding: 0
        iconSource: UM.Theme.getIcon("LinkExternal")
        isIconOnRightSide: true
        height: fontMetrics.height

        onClicked: Qt.openUrlExternally(readMoreUrl)
    }
}