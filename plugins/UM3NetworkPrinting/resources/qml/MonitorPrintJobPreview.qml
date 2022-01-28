// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 2.0
import UM 1.3 as UM

// TODO: Documentation!
Item
{
    id: printJobPreview

    property var printJob: null
    property var size: 256

    width: size
    height: size

    Rectangle
    {
        anchors.fill: parent
        color: printJob ? "transparent" : UM.Theme.getColor("monitor_skeleton_loading")
        radius: 8 // TODO: Theme!
        Image
        {
            id: previewImage
            anchors.fill: parent
            opacity:
            {
                if (printJob && (printJob.state == "error" || printJob.configurationChanges.length > 0 || !printJob.isActive))
                {
                    return 0.5
                }
                return 1.0
            }
            source: printJob ? printJob.previewImageUrl : ""
        }
    }


    UM.RecolorImage
    {
        id: ultiBotImage

        anchors.centerIn: printJobPreview
        color: UM.Theme.getColor("monitor_placeholder_image")
        height: printJobPreview.height
        source: "../svg/ultibot.svg"
        sourceSize
        {
            height: height
            width: width
        }
        /* Since print jobs ALWAYS have an image url, we have to check if that image URL errors or
            not in order to determine if we show the placeholder (ultibot) image instead. */
        visible: printJob && previewImage.status == Image.Error
        width: printJobPreview.width
    }

    UM.RecolorImage
    {
        id: overlayIcon
        anchors.centerIn: printJobPreview
        color: UM.Theme.getColor("monitor_image_overlay")
        height: 0.5 * printJobPreview.height
        source:
        {
            if (!printJob)
            {
                return ""
            }
            if (printJob.configurationChanges.length > 0)
            {
                return "../svg/Warning.svg"
            }
            switch(printJob.state)
            {
                case "error":
                    return "../svg/CancelCircle.svg"
                case "wait_cleanup":
                    return printJob.timeTotal > printJob.timeElapsed ? "../svg/CancelCircle.svg" : ""
                case "pausing":
                    return "../svg/PauseCircle.svg"
                case "paused":
                    return "../svg/PauseCircle.svg"
                case "resuming":
                    return "../svg/PauseCircle.svg"
                default:
                    return ""
            }
            return ""
        }
        sourceSize
        {
            height: height
            width: width
        }
        visible: source != ""
        width: 0.5 * printJobPreview.width
    }
}
