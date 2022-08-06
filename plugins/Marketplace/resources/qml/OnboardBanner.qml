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
    property alias icon: onboardingIcon.source
    property alias text: infoText.text
    property var onRemove
    property string readMoreUrl

    implicitHeight: childrenRect.height + 2 * UM.Theme.getSize("default_margin").height
    color: UM.Theme.getColor("action_panel_secondary")

    UM.ColorImage
    {
        id: onboardingIcon
        anchors
        {
            top: parent.top
            left: parent.left
            margins: UM.Theme.getSize("default_margin").width
        }
        width: UM.Theme.getSize("banner_icon_size").width
        height: UM.Theme.getSize("banner_icon_size").height

        color: UM.Theme.getColor("primary_text")
    }

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

        onClicked: onRemove()
    }

    UM.Label
    {
        id: infoText
        anchors
        {
            top: parent.top
            left: onboardingIcon.right
            right: onboardingClose.left
            margins: UM.Theme.getSize("default_margin").width
        }

        color: UM.Theme.getColor("primary_text")
        elide: Text.ElideRight

        onLineLaidOut: (line) =>
        {
            if(line.isLast)
            {
                // Check if read more button still fits after the body text
                if (line.implicitWidth + readMoreButton.width + UM.Theme.getSize("default_margin").width > width)
                {
                    // If it does place it after the body text
                    readMoreButton.anchors.bottomMargin = -(fontMetrics.height);
                    readMoreButton.anchors.leftMargin = UM.Theme.getSize("thin_margin").width;
                }
                else
                {
                    // Otherwise place it under the text
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
        id: readMoreButton
        anchors.left: infoText.left
        anchors.bottom: infoText.bottom
        text: catalog.i18nc("@button:label", "Learn More")
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