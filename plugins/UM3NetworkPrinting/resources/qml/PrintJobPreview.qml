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
    height: 100;
    width: height;

    // Skeleton
    Rectangle {
        visible: !job;
        anchors.fill: parent;
        radius: UM.Theme.getSize("default_margin").width; // TODO: Theme!
        color: UM.Theme.getColor("viewport_background"); // TODO: Theme!
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
        source: "../svg/ultibot.svg";
        /* Since print jobs ALWAYS have an image url, we have to check if that image URL errors or
            not in order to determine if we show the placeholder (ultibot) image instead. */
        visible: job && previewImage.status == Image.Error;
        width: parent.width;
        height: parent.height;
        sourceSize.width: width;
        sourceSize.height: height;
        color: UM.Theme.getColor("monitor_tab_placeholder_image"); // TODO: Theme!
    }

    UM.RecolorImage {
        id: statusImage;
        anchors.centerIn: parent;
        source: job && job.state == "error" ? "../svg/aborted-icon.svg" : "";
        visible: source != "";
        width: 0.5 * parent.width;
        height: 0.5 * parent.height;
        sourceSize.width: width;
        sourceSize.height: height;
        color: "black";
    }
}