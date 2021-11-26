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
            source: UM.Theme.getIcon("Shop")
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
        onClicked: confirmDeleteDialog.visible = true
    }

    // Body
    Text {
        anchors
        {
            top: parent.top
            left: onboardingIcon.right
            right: onboardingClose.left
            margins: UM.Theme.getSize("default_margin").width
        }

        font: UM.Theme.getFont("medium")
        color: UM.Theme.getColor("primary_text")
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@text", "Streamline your workflow and customize your Ultimaker Cura experience with plugins contributed by our amazing community of users.")
    }
}