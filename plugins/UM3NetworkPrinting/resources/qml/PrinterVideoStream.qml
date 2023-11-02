// Copyright (c) 2023 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import UM 1.3 as UM
import Cura 1.0 as Cura

Item {
    property string cameraUrl: "";

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
        iconSource: UM.Theme.getIcon("Cancel");
        z: 999;
    }

    Cura.NetworkMJPGImage {
        id: cameraImage
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter

        readonly property real img_scale_factor: {
            if (imageWidth > maximumWidth || imageHeight > maximumHeight) {
                return Math.min(maximumWidth / imageWidth, maximumHeight / imageHeight);
            }
            return 1.0;
        }

        width: imageWidth === 0 ? 800 * screenScaleFactor : imageWidth * img_scale_factor
        height: imageHeight === 0 ? 600 * screenScaleFactor : imageHeight * img_scale_factor

        onVisibleChanged: {
            if (cameraUrl === "") return;

            if (visible) {
                start();
            } else {
                stop();
            }
        }
        source: cameraUrl
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
