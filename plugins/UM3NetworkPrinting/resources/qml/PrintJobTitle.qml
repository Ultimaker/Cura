// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 2.0
import UM 1.3 as UM

Column {
    property var job: null;
    height: childrenRect.height;
    spacing: Math.floor( UM.Theme.getSize("default_margin").height / 2); // TODO: Use explicit theme size
    width: parent.width;

    Item {
        id: jobName;
        height: UM.Theme.getSize("monitor_text_line").height;
        width: parent.width;

        // Skeleton loading
        Rectangle {
            color: UM.Theme.getColor("monitor_skeleton_fill");
            height: parent.height;
            visible: !job;
            width: Math.round(parent.width / 3);
        }

        Label {
            anchors.fill: parent;
            color: UM.Theme.getColor("text");
            elide: Text.ElideRight;
            font: UM.Theme.getFont("default_bold");
            text: job && job.name ? job.name : "";
            visible: job;
        }
    }

    Item {
        id: ownerName;
        height: UM.Theme.getSize("monitor_text_line").height;
        width: parent.width;

        // Skeleton loading
        Rectangle {
            color: UM.Theme.getColor("monitor_skeleton_fill");
            height: parent.height;
            visible: !job;
            width: Math.round(parent.width / 2);
        }

        Label {
            anchors.fill: parent;
            color: UM.Theme.getColor("text")
            elide: Text.ElideRight;
            font: UM.Theme.getFont("default");
            text: job ? job.owner : "";
            visible: job;
        }
    }
}