// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Dialogs 1.1
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.3
import QtGraphicalEffects 1.0
import QtQuick.Controls 1.4 as LegacyControls
import UM 1.3 as UM

// Includes print job name, owner, and preview

Item {
    property var job: null;
    property var useUltibot: false;
    height: 100 * screenScaleFactor;
    width: height;

    // Skeleton
    Rectangle {
        anchors.fill: parent;
        color: UM.Theme.getColor("monitor_skeleton_fill");
        radius: UM.Theme.getSize("default_margin").width;
        visible: !job;
    }

    // Actual content
    Image {
        id: previewImage;
        visible: job;
        source: job ? job.previewImageUrl : "";
        opacity: {
            if (job == null) {
                return 1.0;
            }
            var states = ["wait_cleanup", "wait_user_action", "error", "paused"];
            if (states.indexOf(job.state) !== -1) {
                return 0.5;
            }
            return 1.0;
        }
        anchors.fill: parent;
    }

    UM.RecolorImage {
        id: ultibotImage;
        anchors.centerIn: parent;
        color: UM.Theme.getColor("monitor_placeholder_image"); // TODO: Theme!
        height: parent.height;
        source: "../svg/ultibot.svg";
        sourceSize {
            height: height;
            width: width;
        }
        /* Since print jobs ALWAYS have an image url, we have to check if that image URL errors or
            not in order to determine if we show the placeholder (ultibot) image instead. */
        visible: job && previewImage.status == Image.Error;
        width: parent.width;
    }

    UM.RecolorImage {
        id: statusImage;
        anchors.centerIn: parent;
        color: "black"; // TODO: Theme!
        height: Math.round(0.5 * parent.height);
        source: job && job.state == "error" ? "../svg/aborted-icon.svg" : "";
        sourceSize {
            height: height;
            width: width;
        }
        visible: source != "";
        width: Math.round(0.5 * parent.width);
    }
}