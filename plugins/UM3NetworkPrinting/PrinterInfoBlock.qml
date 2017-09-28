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
        var hours = Math.floor(time / 3600)
        time -= hours * 3600
        var minutes = Math.floor(time / 60);
        time -= minutes * 60
        var seconds = Math.floor(time);

        var finalTime = strPadLeft(hours, "0", 2) + ':' + strPadLeft(minutes,'0',2)+ ':' + strPadLeft(seconds,'0',2);
        return finalTime;
    }

    function formatPrintJobPercent(printJob)
    {
        if (printJob == null)
        {
            return "";
        }
        if (printJob.time_total === 0)
        {
            return "";
        }
        return Math.min(100, Math.round(printJob.time_elapsed / printJob.time_total * 100)) + "%";
    }


    id: printerDelegate
    property var printer

    border.width: UM.Theme.getSize("default_lining").width
    border.color: mouse.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : lineColor
    z: mouse.containsMouse ? 1 : 0  // Push this item up a bit on mouse over to ensure that the highlighted bottom border is visible.

    property var printJob:
    {
        if (printer.reserved_by != null)
        {
            // Look in another list.
            return OutputDevice.printJobsByUUID[printer.reserved_by]
        }
        return OutputDevice.printJobsByPrinterUUID[printer.uuid]
    }

    MouseArea
    {
        id: mouse
        anchors.fill:parent
        onClicked: OutputDevice.selectPrinter(printer.unique_name, printer.friendly_name)
        hoverEnabled: true;

        // Only clickable if no printer is selected
        enabled: OutputDevice.selectedPrinterName == ""
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
            width: parent.width / 3
            height: parent.height

            Label   // Print job name
            {
                id: jobNameLabel
                anchors.top: parent.top
                anchors.left: parent.left
                text: printJob != null ? printJob.name : ""
                font: UM.Theme.getFont("default_bold")
            }

            Label
            {
                id: jobOwnerLabel
                anchors.top: jobNameLabel.bottom
                text: printJob != null ? printJob.owner : ""
                opacity: 0.50
            }

            Label
            {
                id: totalTimeLabel
                anchors.bottom: parent.bottom
                text: printJob != null ? getPrettyTime(printJob.time_total) : ""
                opacity: 0.65
                font: UM.Theme.getFont("default")
            }
        }

        Rectangle
        {
            width: parent.width / 3 * 2
            height: parent.height

            Label   // Friendly machine name
            {
                id: printerNameLabel
                anchors.top: parent.top
                anchors.left: parent.left
                width: parent.width / 2 - UM.Theme.getSize("default_margin").width - showCameraIcon.width
                text: printer.friendly_name
                font: UM.Theme.getFont("default_bold")
                elide: Text.ElideRight
            }

            Label   // Machine variant
            {
                id: printerTypeLabel
                anchors.top: printerNameLabel.bottom
                width: parent.width / 2 - UM.Theme.getSize("default_margin").width
                text: printer.machine_variant
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
                UM.RecolorImage
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    source: "camera-icon.svg"
                    width: sourceSize.width
                    height: sourceSize.height * width / sourceSize.width
                    color: "white"
                }
            }

            Row     // PrintCode config
            {
                id: extruderInfo
                anchors.bottom: parent.bottom

                width: parent.width / 2 - UM.Theme.getSize("default_margin").width
                height: childrenRect.height
                spacing: 10 * screenScaleFactor

                PrintCoreConfiguration
                {
                    id: leftExtruderInfo
                    width: (parent.width-1) / 2
                    printCoreConfiguration: printer.configuration[0]
                }

                Rectangle
                {
                    id: extruderSeperator
                    width: 1 * screenScaleFactor
                    height: parent.height
                    color: lineColor
                }

                PrintCoreConfiguration
                {
                    id: rightExtruderInfo
                    width: (parent.width-1) / 2
                    printCoreConfiguration: printer.configuration[1]
                }
            }

            Rectangle   // Print progress
            {
                id: printProgressArea
                anchors.right: parent.right
                anchors.top: parent.top
                height: showExtended ? parent.height: printProgressTitleBar.height
                width: parent.width / 2 - UM.Theme.getSize("default_margin").width
                border.width: UM.Theme.getSize("default_lining").width
                border.color: lineColor
                radius: cornerRadius
                property var showExtended: {
                    if(printJob!= null)
                    {
                        var extendStates = ["sent_to_printer", "wait_for_configuration", "printing", "pre_print", "post_print", "wait_cleanup", "queued"];
                        return extendStates.indexOf(printJob.status) !== -1;
                    }
                    return ! printer.enabled;
                }
                visible:
                {
                    return true
                }

                Item  // Status and Percent
                {
                    id: printProgressTitleBar
                    width: parent.width
                    //border.width: UM.Theme.getSize("default_lining").width
                    //border.color: lineColor
                    height: 40 * screenScaleFactor
                    anchors.left: parent.left

                    Label
                    {
                        id: statusText
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        anchors.verticalCenter: parent.verticalCenter
                        anchors.right: progressText.left
                        anchors.rightMargin: UM.Theme.getSize("default_margin").width
                        text: {
                            if ( ! printer.enabled)
                            {
                                return catalog.i18nc("@label:status", "Disabled");
                            }

                            if(printJob != null)
                            {
                                switch (printJob.status)
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
                                        if (printJob.configuration_changes_required != null && printJob.configuration_changes_required.length !== 0)
                                        {
                                            return catalog.i18nc("@label:status", "Action required");
                                        }
                                        else
                                        {
                                            return "";
                                        }
                                    case "pausing":
                                    case "paused":
                                        return catalog.i18nc("@label:status", "Paused");
                                    case "resuming":
                                        return catalog.i18nc("@label:status", "Resuming");
                                    case "aborted":
                                        return catalog.i18nc("@label:status", "Print aborted");
                                    default:
                                        return "";
                                }
                            }
                            return catalog.i18nc("@label:status", "Available");
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
                        visible: printJob != null && (["printing", "post_print", "pre_print", "sent_to_printer"].indexOf(printJob.status) !== -1)
                        opacity: 0.65
                        font: UM.Theme.getFont("very_small")
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

                    visible: showExtended

                    Label   // Status detail
                    {
                        text:
                        {
                            if ( ! printer.enabled)
                            {
                                return catalog.i18nc("@label", "Not accepting print jobs");
                            }

                            if(printJob != null)
                            {
                                switch (printJob.status)
                                {
                                case "printing":
                                case "post_print":
                                    return catalog.i18nc("@label", "Finishes at: ") + OutputDevice.getTimeCompleted(printJob.time_total - printJob.time_elapsed)
                                case "wait_cleanup":
                                    return catalog.i18nc("@label", "Clear build plate")
                                case "sent_to_printer":
                                case "pre_print":
                                    return catalog.i18nc("@label", "Preparing to print")
                                case "wait_for_configuration":
                                    return catalog.i18nc("@label", "Not accepting print jobs")
                                case "queued":
                                    if (printJob.configuration_changes_required != undefined)
                                    {
                                        return catalog.i18nc("@label", "Waiting for configuration change");
                                    }
                                default:
                                    return "";
                                }
                            }
                            return "";
                        }
                        elide: Text.ElideRight
                        font: UM.Theme.getFont("default")
                    }

                    Label   // Status 2nd row
                    {
                        text: {
                          if(printJob != null) {
                              if(printJob.status == "printing" || printJob.status == "post_print")
                              {
                                  return OutputDevice.getDateCompleted(printJob.time_total - printJob.time_elapsed)
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
