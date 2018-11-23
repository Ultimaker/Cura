// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Controls 1.4
import UM 1.3 as UM

ProgressBar
{
    property var printJob: null
    property var progress: {
        if (!printJob) {
            return 0;
        }
        var result = printJob.timeElapsed / printJob.timeTotal;
        if (result > 1.0) {
            result = 1.0;
        }
        return result;
    }
    width: 180 * screenScaleFactor // TODO: Theme!
    value: progress;
    style: ProgressBarStyle {
        property var remainingTime: {
            if (!printJob) {
                return 0;
            }
            /* Sometimes total minus elapsed is less than 0. Use Math.max() to prevent remaining
                time from ever being less than 0. Negative durations cause strange behavior such
                as displaying "-1h -1m". */
            return Math.max(printer.activePrintJob.timeTotal - printer.activePrintJob.timeElapsed, 0);
        }
        property var progressText: {
            if (!printJob) {
                return "";
            }
            switch (printJob.state) {
                case "wait_cleanup":
                    if (printJob.timeTotal > printJob.timeElapsed) {
                        return catalog.i18nc("@label:status", "Aborted");
                    }
                    return catalog.i18nc("@label:status", "Finished");
                case "pre_print":
                case "sent_to_printer":
                    return catalog.i18nc("@label:status", "Preparing");
                case "aborted":
                    return catalog.i18nc("@label:status", "Aborted");
                case "wait_user_action":
                    return catalog.i18nc("@label:status", "Aborted");
                case "pausing":
                    return catalog.i18nc("@label:status", "Pausing");
                case "paused":
                    return OutputDevice.formatDuration( remainingTime );
                case "resuming":
                    return catalog.i18nc("@label:status", "Resuming");
                case "queued":
                    return catalog.i18nc("@label:status", "Action required");
                default:
                    return OutputDevice.formatDuration( remainingTime );
            }
        }
        background: Rectangle {
            color: "#e4e4f2" // TODO: Theme!
            implicitHeight: visible ? 8 : 0;
            implicitWidth: 180;
            radius: 4
        }
        progress: Rectangle {
            id: progressItem;
            color: {
                if (!printJob) {
                    return "black";
                }
                var state = printJob.state
                var inactiveStates = [
                    "pausing",
                    "paused",
                    "resuming",
                    "wait_cleanup"
                ];
                if (inactiveStates.indexOf(state) > -1 && remainingTime > 0) {
                    return UM.Theme.getColor("monitor_progress_fill_inactive");
                } else {
                    return "#0a0850" // TODO: Theme!
                }
            }
            radius: 4

            Label {
                id: progressLabel;
                anchors {
                    left: parent.left;
                    leftMargin: getTextOffset();
                }
                text: progressText;
                anchors.verticalCenter: parent.verticalCenter;
                color: progressItem.width + progressLabel.width < control.width ? UM.Theme.getColor("text") : UM.Theme.getColor("monitor_progress_fill_text");
                width: contentWidth;
                font: UM.Theme.getFont("default");
            }

            function getTextOffset() {
                if (progressItem.width + progressLabel.width + 16 < control.width) {
                    return progressItem.width + UM.Theme.getSize("default_margin").width;
                } else {
                    return progressItem.width - progressLabel.width - UM.Theme.getSize("default_margin").width;
                }
            }
        }
    }
}