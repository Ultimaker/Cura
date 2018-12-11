// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.0 as Cura

import "Recommended"
import "Custom"

Item
{
    id: content

    width: UM.Theme.getSize("print_setup_widget").width - 2 * UM.Theme.getSize("default_margin").width
    height: childrenRect.height

    enum Mode
    {
        Recommended = 0,
        Custom = 1
    }

    // Set the current mode index to the value that is stored in the preferences or Recommended mode otherwise.
    property int currentModeIndex:
    {
        var index = Math.round(UM.Preferences.getValue("cura/active_mode"))

        if (index != null && !isNaN(index))
        {
            return index
        }
        return PrintSetupSelectorContents.Mode.Recommended
    }
    onCurrentModeIndexChanged: UM.Preferences.setValue("cura/active_mode", currentModeIndex)

    Item
    {
        id: contents
        // Use the visible property instead of checking the currentModeIndex. That creates a binding that
        // evaluates the new height every time the visible property changes.
        height: recommendedPrintSetup.visible ? recommendedPrintSetup.height : customPrintSetup.height

        anchors
        {
            top: parent.top
            left: parent.left
            right: parent.right
        }

        RecommendedPrintSetup
        {
            id: recommendedPrintSetup
            anchors
            {
                left: parent.left
                right: parent.right
                top: parent.top
            }
            visible: currentModeIndex == PrintSetupSelectorContents.Mode.Recommended
        }

        CustomPrintSetup
        {
            id: customPrintSetup
            anchors
            {
                left: parent.left
                right: parent.right
                top: parent.top
            }
            visible: currentModeIndex == PrintSetupSelectorContents.Mode.Custom
        }
    }

    Rectangle
    {
        id: buttonsSeparator

        // The buttonsSeparator is inside the contents. This is to avoid a double line in the bottom
        anchors.bottom: contents.bottom
        width: parent.width
        height: UM.Theme.getSize("default_lining").height
        color: UM.Theme.getColor("lining")
    }

    Item
    {
        id: buttonRow
        property real padding: UM.Theme.getSize("default_margin").width
        height: childrenRect.height + 2 * padding

        anchors
        {
            top: buttonsSeparator.bottom
            left: parent.left
            right: parent.right
        }

        Cura.SecondaryButton
        {
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.margins: parent.padding
            leftPadding: UM.Theme.getSize("default_margin").width
            rightPadding: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@button", "Recommended")
            iconSource: UM.Theme.getIcon("arrow_left")
            visible: currentModeIndex == PrintSetupSelectorContents.Mode.Custom
            onClicked: currentModeIndex = PrintSetupSelectorContents.Mode.Recommended
        }

        Cura.SecondaryButton
        {
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: UM.Theme.getSize("default_margin").width
            leftPadding: UM.Theme.getSize("default_margin").width
            rightPadding: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@button", "Custom")
            iconSource: UM.Theme.getIcon("arrow_right")
            isIconOnRightSide: true
            visible: currentModeIndex == PrintSetupSelectorContents.Mode.Recommended
            onClicked: currentModeIndex = PrintSetupSelectorContents.Mode.Custom
        }
    }
}