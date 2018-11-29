// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.0 as Cura

Item
{
    id: popup

    width: UM.Theme.getSize("print_setup_widget").width
    height: childrenRect.height

    property int currentModeIndex: -1
    onCurrentModeIndexChanged: UM.Preferences.setValue("cura/active_mode", currentModeIndex)

    // Header of the popup
    Rectangle
    {
        id: header
        height: UM.Theme.getSize("print_setup_widget_header").height
        color: UM.Theme.getColor("action_button_hovered")  // TODO: It's not clear the color that we need to use here

        anchors
        {
            top: parent.top
            right: parent.right
            left: parent.left
        }

        Label
        {
            id: headerLabel
            text: catalog.i18nc("@label", "Print settings")
            font: UM.Theme.getFont("default")
            renderType: Text.NativeRendering
            verticalAlignment: Text.AlignVCenter
            color: UM.Theme.getColor("text")
            height: parent.height

            anchors
            {
                topMargin: UM.Theme.getSize("sidebar_margin").height
                left: parent.left
                leftMargin: UM.Theme.getSize("narrow_margin").height
            }
        }

        Button
        {
            id: closeButton
            width: UM.Theme.getSize("message_close").width
            height: UM.Theme.getSize("message_close").height

            anchors
            {
                right: parent.right
                rightMargin: UM.Theme.getSize("default_margin").width
                verticalCenter: parent.verticalCenter
            }

            contentItem: UM.RecolorImage
            {
                anchors.fill: parent
                sourceSize.width: width
                sourceSize.height: width
                color: UM.Theme.getColor("message_text")
                source: UM.Theme.getIcon("cross1")
            }

            background: Item {}

            onClicked: togglePopup() // Will hide the popup item
        }
    }

    Rectangle
    {
        id: topSeparator

        anchors.bottom: header.bottom
        width: parent.width
        height: UM.Theme.getSize("default_lining").height
        color: UM.Theme.getColor("lining")
    }

    Loader
    {
        id: loader
        width: parent.width
        anchors
        {
            top: header.bottom
        }
        sourceComponent: currentModeIndex == 0 ? recommendedPrintSetup : customPrintSetup
    }

    Rectangle
    {
        id: buttonsSeparator

        anchors.top: loader.bottom
        width: parent.width
        height: UM.Theme.getSize("default_lining").height
        color: UM.Theme.getColor("lining")
    }

    Item
    {
        id: buttonRow
        height: childrenRect.height

        // The buttonsSeparator is inside the buttonRow. This is to avoid some weird behaviours with the scroll bar.
        anchors
        {
            top: buttonsSeparator.top
            left: parent.left
            right: parent.right
        }

        Cura.SecondaryButton
        {
            anchors.left: parent.left
            leftPadding: UM.Theme.getSize("default_margin").width
            rightPadding: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@button", "Recommended")
            visible: currentModeIndex == 1
            onClicked: currentModeIndex = 0
        }

        Cura.SecondaryButton
        {
            anchors.right: parent.right
            leftPadding: UM.Theme.getSize("default_margin").width
            rightPadding: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@button", "Custom")
            visible: currentModeIndex == 0
            onClicked: currentModeIndex = 1
        }
    }

    Component
    {
        id: recommendedPrintSetup
        RecommendedPrintSetup
        {
            onShowTooltip: base.showTooltip(item, location, text)
            onHideTooltip: base.hideTooltip()
        }
    }

    Component
    {
        id: customPrintSetup
        CustomPrintSetup
        {
            onShowTooltip: base.showTooltip(item, location, text)
            onHideTooltip: base.hideTooltip()
        }
    }


    Component.onCompleted:
    {
        var index = Math.round(UM.Preferences.getValue("cura/active_mode"))

        if(index != null && !isNaN(index))
        {
            currentModeIndex = index
        }
        else
        {
            currentModeIndex = 0
        }
    }
}