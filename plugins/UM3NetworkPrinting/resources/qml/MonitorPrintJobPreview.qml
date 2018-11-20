// Copyright (c) 2018 Ultimaker B.V.
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

    // Actual content
    Image
    {
        id: previewImage
        anchors.fill: parent
        opacity: printJob && printJob.state == "error" ? 0.5 : 1.0
        source: printJob ? printJob.previewImageUrl : ""
        visible: printJob
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
        id: statusImage
        anchors.centerIn: printJobPreview
        color: UM.Theme.getColor("monitor_image_overlay")
        height: 0.5 * printJobPreview.height
        source: printJob && printJob.state == "error" ? "../svg/aborted-icon.svg" : ""
        sourceSize
        {
            height: height
            width: width
        }
        visible: source != ""
        width: 0.5 * printJobPreview.width
    }
}