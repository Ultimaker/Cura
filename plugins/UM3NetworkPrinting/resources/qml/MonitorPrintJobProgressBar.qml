// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import UM 1.5 as UM

/**
 * NOTE: For most labels, a fixed height with vertical alignment is used to make
 * layouts more deterministic (like the fixed-size textboxes used in original
 * mock-ups). This is also a stand-in for CSS's 'line-height' property. Denoted
 * with '// FIXED-LINE-HEIGHT:'.
 */
Item
{
    id: base

    // The print job which all other information is derived from
    property var printJob: null

    width: childrenRect.width
    height: percentLabel.height

    UM.ProgressBar
    {
        id: progressBar
        anchors
        {
            verticalCenter: parent.verticalCenter
            left: parent.left
        }
        value: printJob ? printJob.progress : 0
        width: UM.Theme.getSize("monitor_progress_bar").width
    }

    UM.Label
    {
        id: percentLabel
        anchors
        {
            left: progressBar.right
            leftMargin: UM.Theme.getSize("default_margin").width
        }
        text: printJob ? Math.round(printJob.progress * 100) + "%" : "0%"
        color: printJob && printJob.isActive ? UM.Theme.getColor("text") : UM.Theme.getColor("monitor_text_disabled")
        width: contentWidth
        wrapMode: Text.NoWrap
    }
    UM.Label
    {
        id: statusLabel
        anchors
        {
            left: percentLabel.right
            leftMargin: UM.Theme.getSize("default_margin").width
        }
        wrapMode: Text.NoWrap
        text:
        {
            if (!printJob)
            {
                return "";
            }
            switch (printJob.state)
            {
                case "wait_cleanup":
                    // This hack was removed previously. Then we found out that we don't get back 'aborted_wait_cleanup'
                    // for the UM2+C it seems. Will communicate this to other teams, in the mean time, put this back.
                    if (printJob.timeTotal > printJob.timeElapsed)
                    {
                        return catalog.i18nc("@label:status", "Aborted");
                    }
                    return catalog.i18nc("@label:status", "Finished");
                case "finished":
                    return catalog.i18nc("@label:status", "Finished");
                case "sent_to_printer":
                    return catalog.i18nc("@label:status", "Preparing...");
                case "pre_print":
                    return catalog.i18nc("@label:status", "Preparing...");
                case "aborting": // NOTE: Doesn't exist but maybe should someday
                    return catalog.i18nc("@label:status", "Aborting...");
                case "aborted": // NOTE: Unused, see above
                    return catalog.i18nc("@label:status", "Aborted");
                case "aborted_post_print":
                    return catalog.i18nc("@label:status", "Aborted");
                case "aborted_wait_user_action":
                    return catalog.i18nc("@label:status", "Aborted");
                case "aborted_wait_cleanup":
                    return catalog.i18nc("@label:status", "Aborted");
                case "failed":
                    return catalog.i18nc("@label:status", "Failed");
                case "failed_post_print":
                    return catalog.i18nc("@label:status", "Failed");
                case "failed_wait_user_action":
                    return catalog.i18nc("@label:status", "Failed");
                case "failed_wait_cleanup":
                    return catalog.i18nc("@label:status", "Failed");
                case "pausing":
                    return catalog.i18nc("@label:status", "Pausing...");
                case "paused":
                    return catalog.i18nc("@label:status", "Paused");
                case "resuming":
                    return catalog.i18nc("@label:status", "Resuming...");
                case "queued":
                    return catalog.i18nc("@label:status", "Action required");
                default:
                    return catalog.i18nc("@label:status", "Finishes %1 at %2").arg(OutputDevice.getDateCompleted(printJob.timeRemaining)).arg(OutputDevice.getTimeCompleted(printJob.timeRemaining));
            }
        }
        width: contentWidth
    }
}
