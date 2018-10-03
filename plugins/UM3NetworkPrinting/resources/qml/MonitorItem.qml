// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import UM 1.3 as UM
import Cura 1.0 as Cura

Component {
    Item {
        height: maximumHeight;
        width: maximumWidth;

        Image {
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
            height: Math.floor((sourceSize.height === 0 ? 600 * screenScaleFactor : sourceSize.height) * width / sourceSize.width);
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
            source: {
                if (OutputDevice.activePrinter != null && OutputDevice.activePrinter.camera != null && OutputDevice.activePrinter.camera.latestImage) {
                    return OutputDevice.activePrinter.camera.latestImage;
                }
                return "";
            }
            width: Math.min(sourceSize.width === 0 ? 800 * screenScaleFactor : sourceSize.width, maximumWidth);
            z: 1;
        }
    }
}