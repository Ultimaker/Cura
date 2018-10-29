// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import UM 1.3 as UM
import Cura 1.0 as Cura

Component {
    Item {
        height: maximumHeight;
        width: maximumWidth;

        Cura.CameraView {
            id: cameraImage;
            anchors {
                horizontalCenter: parent.horizontalCenter;
                verticalCenter: parent.verticalCenter;
            }
            Component.onCompleted: {
                if (OutputDevice.activePrinter != null && OutputDevice.activePrinter.camera != null) {
                    OutputDevice.activePrinter.camera.start();
                }
            }
            height: Math.floor((imageHeight === 0 ? 600 * screenScaleFactor : imageHeight) * width / imageWidth);
            onVisibleChanged: {
                if (visible) {
                    if (OutputDevice.activePrinter != null && OutputDevice.activePrinter.camera != null) {
                        OutputDevice.activePrinter.camera.start();
                    }
                } else {
                    if (OutputDevice.activePrinter != null && OutputDevice.activePrinter.camera != null) {
                        OutputDevice.activePrinter.camera.stop();
                    }
                }
            }
            width: Math.min(imageWidth === 0 ? 800 * screenScaleFactor : imageWidth, maximumWidth);
            z: 1;

            Connections
            {
                target: OutputDevice.activePrinter.camera;
                onNewImage:
                {
                    if (cameraImage.visible) {
                        cameraImage.image = OutputDevice.activePrinter.camera.latestImage;
                        cameraImage.update();
                    }
                }
            }
        }
    }
}