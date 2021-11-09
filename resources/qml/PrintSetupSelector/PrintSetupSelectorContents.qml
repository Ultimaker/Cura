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

    property int absoluteMinimumHeight: 200 * screenScaleFactor

    width: UM.Theme.getSize("print_setup_widget").width - 2 * UM.Theme.getSize("default_margin").width
    height: contents.height + buttonRow.height

    enum Mode
    {
        Recommended = 0,
        Custom = 1
    }

    // Catch all mouse events
    MouseArea
    {
        anchors.fill: parent
        hoverEnabled: true
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
            height: UM.Preferences.getValue("view/settings_list_height") - UM.Theme.getSize("default_margin").height
            Connections
            {
                target: UM.Preferences
                function onPreferenceChanged(preference)
                {
                    if (preference !== "view/settings_list_height" && preference !== "general/window_height" && preference !== "general/window_state")
                    {
                        return;
                    }

                    customPrintSetup.height =
                        Math.min
                        (
                            UM.Preferences.getValue("view/settings_list_height"),
                            Math.max
                            (
                                absoluteMinimumHeight,
                                base.height - (customPrintSetup.mapToItem(null, 0, 0).y + buttonRow.height + UM.Theme.getSize("default_margin").height)
                            )
                        );

                    updateDragPosition();
                }
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
        height: recommendedButton.height + 2 * padding + (draggableArea.visible ? draggableArea.height : 0)

        anchors
        {
            bottom: parent.bottom
            left: parent.left
            right: parent.right
        }

        Cura.SecondaryButton
        {
            id: recommendedButton
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.margins: parent.padding
            leftPadding: UM.Theme.getSize("default_margin").width
            rightPadding: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@button", "Recommended")
            iconSource: UM.Theme.getIcon("ChevronSingleLeft")
            visible: currentModeIndex == PrintSetupSelectorContents.Mode.Custom
            onClicked: currentModeIndex = PrintSetupSelectorContents.Mode.Recommended
        }

        Cura.SecondaryButton
        {
            id: customSettingsButton
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.margins: UM.Theme.getSize("default_margin").width
            leftPadding: UM.Theme.getSize("default_margin").width
            rightPadding: UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@button", "Custom")
            iconSource: UM.Theme.getIcon("ChevronSingleRight")
            isIconOnRightSide: true
            visible: currentModeIndex == PrintSetupSelectorContents.Mode.Recommended
            onClicked:
            {
                currentModeIndex = PrintSetupSelectorContents.Mode.Custom
                updateDragPosition();
            }
        }

        //Invisible area at the bottom with which you can resize the panel.
        MouseArea
        {
            id: draggableArea
            anchors
            {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: childrenRect.height
            cursorShape: Qt.SplitVCursor
            visible: currentModeIndex == PrintSetupSelectorContents.Mode.Custom
            drag
            {
                target: parent
                axis: Drag.YAxis
            }
            onMouseYChanged:
            {
                if(drag.active)
                {
                    // position of mouse relative to dropdown  align vertical centre of mouse area to cursor
                    //      v------------------------------v   v------------v
                    var h = mouseY + buttonRow.y + content.y - height / 2 | 0;
                    if(h < absoluteMinimumHeight) //Enforce a minimum size.
                    {
                        h = absoluteMinimumHeight;
                    }

                    //Absolute mouse Y position in the window, to prevent it from going outside the window.
                    var mouse_absolute_y = mapToGlobal(mouseX, mouseY).y - UM.Preferences.getValue("general/window_top");
                    if(mouse_absolute_y > base.height)
                    {
                        h -= mouse_absolute_y - base.height;
                    }
                    // Enforce a minimum size (again).
                    // This is a bit of a hackish way to do it, but we've seen some occasional reports that the size
                    // could get below the the minimum height.
                    if(h < absoluteMinimumHeight)
                    {
                        h = absoluteMinimumHeight;
                    }
                    UM.Preferences.setValue("view/settings_list_height", h);
                }
            }

            Rectangle
            {
                width: parent.width
                height: UM.Theme.getSize("narrow_margin").height
                color: UM.Theme.getColor("secondary")

                Rectangle
                {
                    anchors.bottom: parent.top
                    width: parent.width
                    height: UM.Theme.getSize("default_lining").height
                    color: UM.Theme.getColor("lining")
                }

                UM.RecolorImage
                {
                    width: UM.Theme.getSize("drag_icon").width
                    height: UM.Theme.getSize("drag_icon").height
                    anchors.centerIn: parent

                    source: UM.Theme.getIcon("ThreeDots")
                    color: UM.Theme.getColor("small_button_text")
                }
            }
        }
    }
}
