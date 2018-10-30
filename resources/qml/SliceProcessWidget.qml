// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.1 as UM
import Cura 1.0 as Cura

Column
{
    id: widget

    width: UM.Theme.getSize("action_panel_button").width

    spacing: UM.Theme.getSize("thin_margin").height

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    property real progress: UM.Backend.progress
    property int backendState: UM.Backend.state

    Item
    {
        id: message
        width: parent.width
        height: childrenRect.height
        visible: widget.backendState == 4

        UM.RecolorImage
        {
            id: warningImage

            anchors.left: parent.left

            source: UM.Theme.getIcon("warning")
            width: UM.Theme.getSize("section_icon").width
            height: UM.Theme.getSize("section_icon").height

            sourceSize.width: width
            sourceSize.height: height

            color: UM.Theme.getColor("warning")
        }

        Label
        {
            id: unableToSliceLabel
            anchors.left: warningImage.right
            anchors.leftMargin: UM.Theme.getSize("thin_margin").width
            text: catalog.i18nc("@label:PrintjobStatus", "Unable to Slice")
            color: UM.Theme.getColor("warning")
            font: UM.Theme.getFont("very_small")
        }
    }

    // Progress bar, only visible when the backend is in the process of slice the printjob
    ProgressBar
    {
        id: progressBar
        width: parent.width
        height: UM.Theme.getSize("progressbar").height
        value: progress
        visible: widget.backendState == 2

        background: Rectangle
        {
            anchors.fill: parent
            radius: UM.Theme.getSize("progressbar_radius").width
            color: UM.Theme.getColor("progressbar_background")
        }

        contentItem: Item
        {
            anchors.fill: parent
            Rectangle
            {
                width: progressBar.visualPosition * parent.width
                height: parent.height
                radius: UM.Theme.getSize("progressbar_radius").width
                color: UM.Theme.getColor("progressbar_control")
            }
        }
    }

    Cura.ActionButton
    {
        id: prepareButton
        width: parent.width
        height: UM.Theme.getSize("action_panel_button").height
        text: autoSlice ? catalog.i18nc("@button", "Auto slicing...") : (widget.backendState == 1 ? catalog.i18nc("@button", "Slice") : catalog.i18nc("@button", "Cancel"))
        enabled: !autoSlice

        // Get the current value from the preferences
        property bool autoSlice: UM.Preferences.getValue("general/auto_slice")

        disabledColor: "transparent"
        textDisabledColor: UM.Theme.getColor("primary")
        outlineDisabledColor: "transparent"

        onClicked:
        {
            if ([1, 5].indexOf(widget.backendState) != -1)
            {
                CuraApplication.backend.forceSlice()
            }
            else
            {
                CuraApplication.backend.stopSlicing()
            }
        }
    }

    // React when the user changes the preference of having the auto slice enabled
    Connections
    {
        target: UM.Preferences
        onPreferenceChanged:
        {
            var autoSlice = UM.Preferences.getValue("general/auto_slice")
            prepareButton.autoSlice = autoSlice
        }
    }
}
