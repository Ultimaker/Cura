// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4
import UM 1.3 as UM

Item {
    property var camera: null;

    Rectangle {
        anchors.fill:parent;
        color: UM.Theme.getColor("viewport_overlay");
        opacity: 0.5;
    }

    MouseArea {
        anchors.fill: parent;
        onClicked: OutputDevice.setActiveCamera(null);
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

    Image {
        id: cameraImage
        anchors.horizontalCenter: parent.horizontalCenter;
        anchors.verticalCenter: parent.verticalCenter;
        height: Math.round((sourceSize.height === 0 ? 600 * screenScaleFactor : sourceSize.height) * width / sourceSize.width);
        onVisibleChanged: {
            if (visible) {
                if (camera != null) {
                    camera.start();
                }
            } else {
                if (camera != null) {
                    camera.stop();
                }
            }
        }
        source: {
            if (camera != null && camera.latestImage != null) {
                return camera.latestImage;
            }
            return "";
        }
        width: Math.min(sourceSize.width === 0 ? 800 * screenScaleFactor : sourceSize.width, maximumWidth);
        z: 1
    }

    MouseArea {
        anchors.fill: cameraImage;
        onClicked: {
            OutputDevice.setActiveCamera(null);
        }
        z: 1;
    }
}
