// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls.Styles 1.3
import QtQuick.Controls 1.4
import UM 1.3 as UM

/**
 * NOTE: For most labels, a fixed height with vertical alignment is used to make
 * layouts more deterministic (like the fixed-size textboxes used in original
 * mock-ups). This is also a stand-in for CSS's 'line-height' property. Denoted
 * with '// FIXED-LINE-HEIGHT:'.
 */
Item
{
    id: base
    property var printJob: null
    property var progress:
    {
        if (!printJob)
        {
            return 0
        }
        var result = printJob.timeElapsed / printJob.timeTotal
        if (result > 1.0)
        {
            result = 1.0
        }
        return result
    }
    property var remainingTime:
    {
        if (!printJob) {
            return 0
        }
        /* Sometimes total minus elapsed is less than 0. Use Math.max() to prevent remaining
            time from ever being less than 0. Negative durations cause strange behavior such
            as displaying "-1h -1m". */
        return Math.max(printer.activePrintJob.timeTotal - printer.activePrintJob.timeElapsed, 0)
    }
    property var progressText:
    {
        if (!printJob)
        {
            return "";
        }
        switch (printJob.state)
        {
            case "wait_cleanup":
                if (printJob.timeTotal > printJob.timeElapsed)
                {
                    return catalog.i18nc("@label:status", "Aborted")
                }
                return catalog.i18nc("@label:status", "Finished")
            case "pre_print":
            case "sent_to_printer":
                return catalog.i18nc("@label:status", "Preparing")
            case "aborted":
                return catalog.i18nc("@label:status", "Aborted")
            case "wait_user_action":
                return catalog.i18nc("@label:status", "Aborted")
            case "pausing":
                return catalog.i18nc("@label:status", "Pausing")
            case "paused":
                return OutputDevice.formatDuration( remainingTime )
            case "resuming":
                return catalog.i18nc("@label:status", "Resuming")
            case "queued":
                return catalog.i18nc("@label:status", "Action required")
            default:
                return OutputDevice.formatDuration( remainingTime )
        }
    }
    width: childrenRect.width
    height: 18 * screenScaleFactor // TODO: Theme!

    ProgressBar
    {
        id: progressBar
        anchors
        {
            verticalCenter: parent.verticalCenter
        }
        value: progress;
        style: ProgressBarStyle
        {
            background: Rectangle
            {
                color: "#e4e4f2" // TODO: Theme!
                implicitHeight: visible ? 8 * screenScaleFactor : 0 // TODO: Theme!
                implicitWidth: 180 * screenScaleFactor // TODO: Theme!
                radius: 4 * screenScaleFactor // TODO: Theme!
            }
            progress: Rectangle
            {
                id: progressItem;
                color:
                {
                    if (printJob)
                    {
                        var state = printJob.state
                        var inactiveStates = [
                            "pausing",
                            "paused",
                            "resuming",
                            "wait_cleanup"
                        ]
                        if (inactiveStates.indexOf(state) > -1 && remainingTime > 0)
                        {
                            return UM.Theme.getColor("monitor_progress_fill_inactive")
                        }
                    }
                    return "#0a0850" // TODO: Theme!
                }
                radius: 4 * screenScaleFactor // TODO: Theme!
            }
        }
    }
    Label
    {
        id: progressLabel
        anchors
        {
            left: progressBar.right
            leftMargin: 18 * screenScaleFactor // TODO: Theme!
        }
        text: progressText
        color: "#374355" // TODO: Theme!
        width: contentWidth
        font: UM.Theme.getFont("medium") // 14pt, regular

        // FIXED-LINE-HEIGHT:
        height: 18 * screenScaleFactor // TODO: Theme!
        verticalAlignment: Text.AlignVCenter
    }
}