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
        height: UM.Theme.getSize("monitor_tab_text_line").height;
        width: parent.width;

        Rectangle {
            color: UM.Theme.getColor("viewport_background"); // TODO: Use explicit theme color
            height: parent.height;
            visible: !job;
            width: parent.width / 3;
        }

        Label {
            anchors.fill: parent;
            elide: Text.ElideRight;
            font: UM.Theme.getFont("default_bold");
            text: job ? job.name : "";
            visible: job;
        }
    }

    Item {
        id: ownerName;
        height: UM.Theme.getSize("monitor_tab_text_line").height;
        width: parent.width;

        Rectangle {
            color: UM.Theme.getColor("viewport_background"); // TODO: Use explicit theme color
            height: parent.height;
            visible: !job;
            width: parent.width / 2;
        }

        Label {
            anchors.fill: parent;
            elide: Text.ElideRight;
            font: UM.Theme.getFont("default");
            text: job ? job.owner : "";
            visible: job;
        }
    }
}