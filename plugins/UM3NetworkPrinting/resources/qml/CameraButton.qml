// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.3
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.3
import UM 1.3 as UM
import Cura 1.0 as Cura

Rectangle {
    property var iconSource: null;
    color: clickArea.containsMouse ? UM.Theme.getColor("primary_hover") : UM.Theme.getColor("primary");
    height: width;
    radius: 0.5 * width;
    width: 36 * screenScaleFactor;

    UM.RecolorImage {
        id: icon;
        anchors {
            horizontalCenter: parent.horizontalCenter;
            verticalCenter: parent.verticalCenter;
        }
        color: UM.Theme.getColor("primary_text");
        height: width;
        source: iconSource;
        width: parent.width / 2;
    }

    MouseArea {
        id: clickArea;
        anchors.fill: parent;
        hoverEnabled: true;
        onClicked: {
            if (OutputDevice.activeCamera !== null) {
                OutputDevice.setActiveCamera(null)
            } else {
                OutputDevice.setActiveCamera(modelData.camera);
            }
        }
    }
}