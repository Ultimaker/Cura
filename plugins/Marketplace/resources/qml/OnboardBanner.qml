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
    property var bannerType

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
            source: {
                switch (bannerType) {
                    case "__PLUGINS__" : return UM.Theme.getIcon("Shop");
                    case "__MATERIALS__" : return UM.Theme.getIcon("Spool");
                    case "__MANAGE_PACKAGES__" : return UM.Theme.getIcon("ArrowDoubleCircleRight");
                    default: return "";
                }
            }
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
        text: {
            switch (bannerType) {
                case "__PLUGINS__" : return catalog.i18nc("@text", "Streamline your workflow and customize your Ultimaker Cura experience with plugins contributed by our amazing community of users.");
                case "__MATERIALS__" : return catalog.i18nc("@text", "Select and install material profiles optimised for your Ultimaker 3D printers.");
                case "__MANAGE_PACKAGES__" : return catalog.i18nc("@text", "Manage your Ultimaker Cura plugins and material profiles here. Make sure to keep your plugins up to date and backup your setup regularly.");
                default: return "";
            }
        }
    }
}