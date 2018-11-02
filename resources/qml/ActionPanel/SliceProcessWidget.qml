// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3
import QtQuick.Controls 1.4 as Controls1

import UM 1.1 as UM
import Cura 1.0 as Cura


// This element contains all the elements the user needs to create a printjob from the
// model(s) that is(are) on the buildplate. Mainly the button to start/stop the slicing
// process and a progress bar to see the progress of the process.
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

    function sliceOrStopSlicing()
    {
        if (widget.backendState == UM.Backend.NotStarted)
        {
            CuraApplication.backend.forceSlice()
        }
        else
        {
            CuraApplication.backend.stopSlicing()
        }
    }

    Cura.IconLabel
    {
        id: message
        width: parent.width
        visible: widget.backendState == UM.Backend.Error

        text: catalog.i18nc("@label:PrintjobStatus", "Unable to Slice")
        source: UM.Theme.getIcon("warning")
        color: UM.Theme.getColor("warning")
        font: UM.Theme.getFont("very_small")
    }

    // Progress bar, only visible when the backend is in the process of slice the printjob
    ProgressBar
    {
        id: progressBar
        width: parent.width
        height: UM.Theme.getSize("progressbar").height
        value: progress
        visible: widget.backendState == UM.Backend.Processing

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
        text:
        {
            if ([UM.Backend.NotStarted, UM.Backend.Error].indexOf(widget.backendState) != -1)
            {
                return catalog.i18nc("@button", "Slice")
            }
            if (autoSlice)
            {
                return catalog.i18nc("@button", "Auto slicing...")
            }
            return catalog.i18nc("@button", "Cancel")
        }
        enabled: !autoSlice && !disabledSlice

        // Get the current value from the preferences
        property bool autoSlice: UM.Preferences.getValue("general/auto_slice")
        // Disable the slice process when
        property bool disabledSlice: [UM.Backend.Done, UM.Backend.Error].indexOf(widget.backendState) != -1

        disabledColor: disabledSlice ? UM.Theme.getColor("action_button_disabled") : "transparent"
        textDisabledColor: disabledSlice ?  UM.Theme.getColor("action_button_disabled_text") : UM.Theme.getColor("primary")
        outlineDisabledColor: disabledSlice ? UM.Theme.getColor("action_button_disabled_border") : "transparent"

        onClicked: sliceOrStopSlicing()
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

    // Shortcut for "slice/stop"
    Controls1.Action
    {
        shortcut: "Ctrl+P"
        onTriggered:
        {
            if (prepareButton.enabled)
            {
                sliceOrStopSlicing()
            }
        }
    }
}
