// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import UM 1.2 as UM

Item {
    property alias text: familyNameLabel.text;
    property var padding: 3 * screenScaleFactor; // TODO: Theme!
    implicitHeight: familyNameLabel.contentHeight + 2 * padding; // Apply the padding to top and bottom.
    implicitWidth: Math.max(48 * screenScaleFactor, familyNameLabel.contentWidth + implicitHeight); // The extra height is added to ensure the radius doesn't cut something off.

    Rectangle {
        id: background;
        anchors {
            horizontalCenter: parent.horizontalCenter;
            right: parent.right;
        }
        color: familyNameLabel.text.length < 1 ? UM.Theme.getColor("monitor_skeleton_fill") : UM.Theme.getColor("monitor_pill_background");
        height: parent.height;
        radius: 0.5 * height;
        width: parent.width;
    }

    Label {
        id: familyNameLabel;
        anchors.centerIn: parent;
        color: UM.Theme.getColor("text");
        text: "";
    }
}