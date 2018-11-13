// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM
import Cura 1.0 as Cura

Item {
    property var cameraUrl: "";

    Rectangle {
        anchors.fill:parent;
        color: UM.Theme.getColor("viewport_overlay");
        opacity: 0.5;
    }

    MouseArea {
        anchors.fill: parent;
        onClicked: OutputDevice.setActiveCameraUrl("");
        z: 0;
    }

    CameraButton {
        id: closeCameraButton;
        anchors {
            right: cameraImage.right
            rightMargin: UM.Theme.getSize("default_margin").width
            top: cameraImage.top
            topMargin: UM.Theme.getSize("default_margin").height
        }
        iconSource: UM.Theme.getIcon("cross1");
        z: 999;
    }

    Cura.NetworkMJPGImage {
        id: cameraImage
        anchors.horizontalCenter: parent.horizontalCenter;
        anchors.verticalCenter: parent.verticalCenter;
        height: Math.round((imageHeight === 0 ? 600 * screenScaleFactor : imageHeight) * width / imageWidth);
        onVisibleChanged: {
            if (visible) {
                if (cameraUrl != "") {
                    start();
                }
            } else {
                if (cameraUrl != "") {
                    stop();
                }
            }
        }
        source: cameraUrl
        width: Math.min(imageWidth === 0 ? 800 * screenScaleFactor : imageWidth, maximumWidth);
        z: 1
    }

    MouseArea {
        anchors.fill: cameraImage;
        onClicked: {
            OutputDevice.setActiveCameraUrl("");
        }
        z: 1;
    }
}
