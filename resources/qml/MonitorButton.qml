// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Dialogs 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM
import Cura 1.0 as Cura

Item
{
    id: base;
    UM.I18nCatalog { id: catalog; name:"cura"}

    property bool printerConnected: Cura.MachineManager.printerOutputDevices.length != 0
    property bool printerAcceptsCommands: printerConnected && Cura.MachineManager.printerOutputDevices[0].acceptsCommands
    property real progress: printerConnected ? Cura.MachineManager.printerOutputDevices[0].progress : 0
    property int backendState: UM.Backend.state

    property bool showProgress: {
        // determine if we need to show the progress bar + percentage
        if(!printerConnected || !printerAcceptsCommands) {
            return false;
        }

        switch(Cura.MachineManager.printerOutputDevices[0].jobState)
        {
            case "printing":
            case "paused":
            case "pausing":
            case "resuming":
                return true;
            case "pre_print":  // heating, etc.
            case "wait_cleanup":
            case "offline":
            case "abort":  // note sure if this jobState actually occurs in the wild
            case "error":  // after clicking abort you apparently get "error"
            case "ready":  // ready to print or getting ready
            case "":  // ready to print or getting ready
            default:
                return false;
        }
    }

    property variant statusColor:
    {
        if(!printerConnected || !printerAcceptsCommands)
            return UM.Theme.getColor("text");

        switch(Cura.MachineManager.printerOutputDevices[0].printerState)
        {
            case "maintenance":
                return UM.Theme.getColor("status_busy");
            case "error":
                return UM.Theme.getColor("status_stopped");
        }

        switch(Cura.MachineManager.printerOutputDevices[0].jobState)
        {
            case "printing":
            case "pre_print":
            case "wait_cleanup":
            case "pausing":
            case "resuming":
                return UM.Theme.getColor("status_busy");
            case "ready":
            case "":
                return UM.Theme.getColor("status_ready");
            case "paused":
                return UM.Theme.getColor("status_paused");
            case "error":
                return UM.Theme.getColor("status_stopped");
            case "offline":
                return UM.Theme.getColor("status_offline");
            default:
                return UM.Theme.getColor("text");
        }
    }

    property bool activity: CuraApplication.platformActivity;
    property string fileBaseName
    property string statusText:
    {
        if(!printerConnected)
            return catalog.i18nc("@label:MonitorStatus", "Not connected to a printer");
        if(!printerAcceptsCommands)
            return catalog.i18nc("@label:MonitorStatus", "Printer does not accept commands");

        var printerOutputDevice = Cura.MachineManager.printerOutputDevices[0]

        if(printerOutputDevice.printerState == "maintenance")
        {
            return catalog.i18nc("@label:MonitorStatus", "In maintenance. Please check the printer");
        }
        switch(printerOutputDevice.jobState)
        {
            case "offline":
                return catalog.i18nc("@label:MonitorStatus", "Lost connection with the printer");
            case "printing":
                return catalog.i18nc("@label:MonitorStatus", "Printing...");
            //TODO: Add text for case "pausing".
            case "paused":
                return catalog.i18nc("@label:MonitorStatus", "Paused");
            //TODO: Add text for case "resuming".
            case "pre_print":
                return catalog.i18nc("@label:MonitorStatus", "Preparing...");
            case "wait_cleanup":
                return catalog.i18nc("@label:MonitorStatus", "Please remove the print");
            case "error":
                return printerOutputDevice.errorText;
            default:
                return " ";
        }
    }

    Label
    {
        id: statusLabel
        width: parent.width - 2 * UM.Theme.getSize("sidebar_margin").width
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width

        color: base.statusColor
        font: UM.Theme.getFont("large")
        text: statusText
    }

    Label
    {
        id: percentageLabel
        anchors.top: parent.top
        anchors.right: progressBar.right

        color: base.statusColor
        font: UM.Theme.getFont("large")
        text: Math.round(progress) + "%"
        visible: showProgress
    }

    ProgressBar
    {
        id: progressBar;
        minimumValue: 0;
        maximumValue: 100;
        value: 0;

        //Doing this in an explicit binding since the implicit binding breaks on occasion.
        Binding
        {
            target: progressBar;
            property: "value";
            value: base.progress;
        }

        visible: showProgress;
        indeterminate:
        {
            if(!printerConnected)
            {
                return false;
            }
            switch(Cura.MachineManager.printerOutputDevices[0].jobState)
            {
                case "pausing":
                case "resuming":
                    return true;
                default:
                    return false;
            }
        }
        style: UM.Theme.styles.progressbar;

        property string backgroundColor: UM.Theme.getColor("progressbar_background");
        property string controlColor: base.statusColor;

        width: parent.width - 2 * UM.Theme.getSize("sidebar_margin").width;
        height: UM.Theme.getSize("progressbar").height;
        anchors.top: statusLabel.bottom;
        anchors.topMargin: UM.Theme.getSize("sidebar_margin").height / 4;
        anchors.left: parent.left;
        anchors.leftMargin: UM.Theme.getSize("sidebar_margin").width;
    }

    Row {
        id: buttonsRow
        height: abortButton.height
        anchors.top: progressBar.bottom
        anchors.topMargin: UM.Theme.getSize("sidebar_margin").height
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("sidebar_margin").width
        spacing: UM.Theme.getSize("default_margin").width

        Row {
            id: additionalComponentsRow
            spacing: UM.Theme.getSize("default_margin").width
        }

        Connections {
            target: Printer
            onAdditionalComponentsChanged:
            {
                if(areaId == "monitorButtons") {
                    for (var component in CuraApplication.additionalComponents["monitorButtons"]) {
                        CuraApplication.additionalComponents["monitorButtons"][component].parent = additionalComponentsRow
                    }
                }
            }
        }

        Button
        {
            id: pauseResumeButton

            height: UM.Theme.getSize("save_button_save_to_button").height

            property bool userClicked: false
            property string lastJobState: ""

            visible: printerConnected && Cura.MachineManager.printerOutputDevices[0].canPause
            enabled: (!userClicked) && printerConnected && Cura.MachineManager.printerOutputDevices[0].acceptsCommands &&
                     (["paused", "printing"].indexOf(Cura.MachineManager.printerOutputDevices[0].jobState) >= 0)

            text: {
                var result = "";
                if (!printerConnected)
                {
                  return "";
                }
                var jobState = Cura.MachineManager.printerOutputDevices[0].jobState;

                if (jobState == "paused")
                {
                    return catalog.i18nc("@label:", "Resume");
                }
                else
                {
                    return catalog.i18nc("@label:", "Pause");
                }
            }
            onClicked:
            {
                var current_job_state = Cura.MachineManager.printerOutputDevices[0].jobState
                if(current_job_state == "paused")
                {
                    Cura.MachineManager.printerOutputDevices[0].setJobState("print");
                }
                else if(current_job_state == "printing")
                {
                    Cura.MachineManager.printerOutputDevices[0].setJobState("pause");
                }
            }

            style: UM.Theme.styles.sidebar_action_button
        }

        Button
        {
            id: abortButton

            visible: printerConnected && Cura.MachineManager.printerOutputDevices[0].canAbort
            enabled: printerConnected && Cura.MachineManager.printerOutputDevices[0].acceptsCommands &&
                     (["paused", "printing", "pre_print"].indexOf(Cura.MachineManager.printerOutputDevices[0].jobState) >= 0)

            height: UM.Theme.getSize("save_button_save_to_button").height

            text: catalog.i18nc("@label:", "Abort Print")
            onClicked: confirmationDialog.visible = true

            style: UM.Theme.styles.sidebar_action_button
        }

        MessageDialog
        {
            id: confirmationDialog

            title: catalog.i18nc("@window:title", "Abort print")
            icon: StandardIcon.Warning
            text: catalog.i18nc("@label", "Are you sure you want to abort the print?")
            standardButtons: StandardButton.Yes | StandardButton.No
            Component.onCompleted: visible = false
            onYes: Cura.MachineManager.printerOutputDevices[0].setJobState("abort")
        }
    }
}
