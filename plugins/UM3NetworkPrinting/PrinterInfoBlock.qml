import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.3 as UM

Rectangle
{
    function strPadLeft(string, pad, length)
    {
        return (new Array(length + 1).join(pad) + string).slice(-length);
    }

    function getPrettyTime(time)
    {
        return OutputDevice.formatDuration(time)
    }

    function formatPrintJobPercent(printJob)
    {
        if (printJob == null)
        {
            return "";
        }
        if (printJob.timeTotal === 0)
        {
            return "";
        }
        return Math.min(100, Math.round(printJob.timeElapsed / printJob.timeTotal * 100)) + "%";
    }

    function printerStatusText(printer)
    {
        switch (printer.state)
        {
            case "pre_print":
                return catalog.i18nc("@label", "Preparing to print")
            case "printing":
                return catalog.i18nc("@label:status", "Printing");
            case "idle":
                return catalog.i18nc("@label:status", "Available");
            case "unreachable":
                return catalog.i18nc("@label:MonitorStatus", "Lost connection with the printer");
            case "maintenance":  // TODO: new string
            case "unknown":
            default:
                return catalog.i18nc("@label Printer status", "Unknown");
        }
    }

    id: printerDelegate

    property var printer: null
    property var printJob: printer != null ? printer.activePrintJob: null

    border.width: UM.Theme.getSize("default_lining").width
    border.color: mouse.containsMouse ? emphasisColor : lineColor
    z: mouse.containsMouse ? 1 : 0  // Push this item up a bit on mouse over to ensure that the highlighted bottom border is visible.

    MouseArea
    {
        id: mouse
        anchors.fill:parent
        onClicked: OutputDevice.setActivePrinter(printer)
        hoverEnabled: true;

        // Only clickable if no printer is selected
        enabled: OutputDevice.activePrinter == null && printer.state !== "unreachable"
    }

    Row
    {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.margins: UM.Theme.getSize("default_margin").width

        Rectangle
        {
            width: Math.round(parent.width / 3)
            height: parent.height

            Label   // Print job name
            {
                id: jobNameLabel
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("default_margin").width

                text: printJob != null ? printJob.name : ""
                font: UM.Theme.getFont("default_bold")
                elide: Text.ElideRight

            }

            Label
            {
                id: jobOwnerLabel
                anchors.top: jobNameLabel.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                text: printJob != null ? printJob.owner : ""
                opacity: 0.50
                elide: Text.ElideRight
            }

            Label
            {
                id: totalTimeLabel
                anchors.bottom: parent.bottom
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                text: printJob != null ? getPrettyTime(printJob.timeTotal) : ""
                opacity: 0.65
                font: UM.Theme.getFont("default")
                elide: Text.ElideRight
            }
        }

        Rectangle
        {
            width: Math.round(parent.width / 3 * 2)
            height: parent.height

            Label   // Friendly machine name
            {
                id: printerNameLabel
                anchors.top: parent.top
                anchors.left: parent.left
                width: Math.round(parent.width / 2 - UM.Theme.getSize("default_margin").width - showCameraIcon.width)
                text: printer.name
                font: UM.Theme.getFont("default_bold")
                elide: Text.ElideRight
            }

            Label   // Machine variant
            {
                id: printerTypeLabel
                anchors.top: printerNameLabel.bottom
                width: Math.round(parent.width / 2 - UM.Theme.getSize("default_margin").width)
                text: printer.type
                anchors.left: parent.left
                elide: Text.ElideRight
                font: UM.Theme.getFont("very_small")
                opacity: 0.50
            }

            Rectangle   // Camera icon
            {
                id: showCameraIcon
                width: 40 * screenScaleFactor
                height: width
                radius: width
                anchors.right: printProgressArea.left
                anchors.rightMargin: UM.Theme.getSize("default_margin").width
                color: emphasisColor
                opacity: printer != null && printer.state === "unreachable" ? 0.3 : 1

                Image
                {
                    width: parent.width
                    height: width
                    anchors.right: parent.right
                    anchors.rightMargin: parent.rightMargin
                    source: "camera-icon.svg"
                }
            }

            Row     // PrintCore config
            {
                id: extruderInfo
                anchors.bottom: parent.bottom

                width: Math.round(parent.width / 2 - UM.Theme.getSize("default_margin").width)
                height: childrenRect.height

                spacing: UM.Theme.getSize("default_margin").width

                PrintCoreConfiguration
                {
                    id: leftExtruderInfo
                    width: Math.round((parent.width - extruderSeperator.width) / 2)
                    printCoreConfiguration: printer.extruders[0]
                }

                Rectangle
                {
                    id: extruderSeperator
                    width: UM.Theme.getSize("default_lining").width
                    height: parent.height
                    color: lineColor
                }

                PrintCoreConfiguration
                {
                    id: rightExtruderInfo
                    width: Math.round((parent.width - extruderSeperator.width) / 2)
                    printCoreConfiguration: printer.extruders[1]
                }
            }

            Rectangle   // Print progress
            {
                id: printProgressArea
                anchors.right: parent.right
                anchors.top: parent.top
                height: showExtended ? parent.height: printProgressTitleBar.height
                width: Math.round(parent.width / 2 - UM.Theme.getSize("default_margin").width)
                border.width: UM.Theme.getSize("default_lining").width
                border.color: lineColor
                radius: cornerRadius
                property var showExtended: {
                    if(printJob != null)
                    {
                        var extendStates = ["sent_to_printer", "wait_for_configuration", "printing", "pre_print", "post_print", "wait_cleanup", "queued"];
                        return extendStates.indexOf(printJob.state) !== -1;
                    }
                    return printer.state == "disabled"
                }

                Item  // Status and Percent
                {
                    id: printProgressTitleBar

                    property var showPercent: {
                        return printJob != null && (["printing", "post_print", "pre_print", "sent_to_printer"].indexOf(printJob.state) !== -1);
                    }

                    width: parent.width
                    //TODO: hardcoded value
                    height: 40 * screenScaleFactor
                    anchors.left: parent.left

                    Label
                    {
                        id: statusText
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        anchors.right: progressText.left
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        anchors.verticalCenter: parent.verticalCenter
                        text: {
                            if (printer.state == "disabled")
                            {
                                return catalog.i18nc("@label:status", "Disabled");
                            }

                            if (printer.state === "unreachable")
                            {
                                return printerStatusText(printer);
                            }

                            if (printJob != null)
                            {
                                switch (printJob.state)
                                {
                                    case "printing":
                                    case "post_print":
                                        return catalog.i18nc("@label:status", "Printing")
                                    case "wait_for_configuration":
                                        return catalog.i18nc("@label:status", "Reserved")
                                    case "wait_cleanup":
                                        return catalog.i18nc("@label:status", "Finished")
                                    case "pre_print":
                                    case "sent_to_printer":
                                        return catalog.i18nc("@label", "Preparing to print")
                                    case "queued":
                                            return catalog.i18nc("@label:status", "Action required");
                                    case "pausing":
                                    case "paused":
                                        return catalog.i18nc("@label:status", "Paused");
                                    case "resuming":
                                        return catalog.i18nc("@label:status", "Resuming");
                                    case "aborted":
                                        return catalog.i18nc("@label:status", "Print aborted");
                                    default:
                                        return printerStatusText(printer);
                                }
                            }
                            return printerStatusText(printer);
                        }

                        elide: Text.ElideRight
                        font: UM.Theme.getFont("small")
                    }

                    Label
                    {
                        id: progressText
                        anchors.right: parent.right
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        anchors.top: statusText.top

                        text: formatPrintJobPercent(printJob)
                        visible: printProgressTitleBar.showPercent
                        //TODO: Hardcoded value
                        opacity: 0.65
                        font: UM.Theme.getFont("very_small")
                    }

                    Image
                    {
                        width: statusText.height
                        height: width
                        anchors.right: parent.right
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        anchors.top: statusText.top

                        visible: !printProgressTitleBar.showPercent

                        source: {
                            if (printer.state == "disabled")
                            {
                                return "blocked-icon.svg";
                            }

                            if (printer.state === "unreachable")
                            {
                                return "";
                            }

                            if (printJob != null)
                            {
                                if(printJob.state === "queued")
                                {
                                    return "action-required-icon.svg";
                                }
                                else if (printJob.state === "wait_cleanup")
                                {
                                    return "checkmark-icon.svg";
                                }
                            }
                            return "";  // We're not going to show it, so it will not be resolved as a url.
                        }
                    }

                    Rectangle
                    {
                        //TODO: This will become a progress bar in the future
                        width: parent.width
                        height: UM.Theme.getSize("default_lining").height
                        anchors.bottom: parent.bottom
                        anchors.left: parent.left
                        visible: printProgressArea.showExtended
                        color: lineColor
                    }
                }

                Column
                {
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width

                    anchors.top: printProgressTitleBar.bottom
                    anchors.topMargin: UM.Theme.getSize("default_margin").height

                    width: parent.width - 2 * UM.Theme.getSize("default_margin").width

                    visible: printProgressArea.showExtended

                    Label   // Status detail
                    {
                        text:
                        {
                            if (printer.state == "disabled")
                            {
                                return catalog.i18nc("@label", "Not accepting print jobs");
                            }

                            if (printer.state === "unreachable")
                            {
                                return "";
                            }

                            if(printJob != null)
                            {
                                switch (printJob.state)
                                {
                                case "printing":
                                case "post_print":
                                    return catalog.i18nc("@label", "Finishes at: ") + OutputDevice.getTimeCompleted(printJob.timeTotal - printJob.timeElapsed)
                                case "wait_cleanup":
                                    return catalog.i18nc("@label", "Clear build plate")
                                case "sent_to_printer":
                                case "pre_print":
                                    return catalog.i18nc("@label", "Preparing to print")
                                case "wait_for_configuration":
                                    return catalog.i18nc("@label", "Not accepting print jobs")
                                case "queued":
                                    return catalog.i18nc("@label", "Waiting for configuration change");
                                default:
                                    return "";
                                }
                            }
                            return "";
                        }
                        anchors.left: parent.left
                        anchors.right: parent.right
                        elide: Text.ElideRight
                        wrapMode: Text.Wrap

                        font: UM.Theme.getFont("default")
                    }

                    Label   // Status 2nd row
                    {
                        text: {
                          if(printJob != null)
                          {
                              if(printJob.state == "printing" || printJob.state == "post_print")
                              {
                                  return OutputDevice.getDateCompleted(printJob.timeTotal - printJob.timeElapsed)
                              }
                          }
                          return "";
                        }

                        elide: Text.ElideRight
                        font: UM.Theme.getFont("default")
                    }
                }
            }
        }
    }
}
