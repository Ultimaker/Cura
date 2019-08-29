// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import UM 1.3 as UM
import Cura 1.0 as Cura

Component {
    Item {
        height: maximumHeight;
        width: maximumWidth;

        Cura.NetworkMJPGImage {
            id: cameraImage;
            anchors {
                horizontalCenter: parent.horizontalCenter;
                verticalCenter: parent.verticalCenter;
            }
            Component.onCompleted: {
                if (OutputDevice.activePrinter != null && OutputDevice.activePrinter.cameraUrl != null) {
                    cameraImage.start();
                }
            }
            height: Math.floor((imageHeight === 0 ? 600 * screenScaleFactor : imageHeight) * width / imageWidth);
            onVisibleChanged: {
                if (visible) {
                    if (OutputDevice.activePrinter != null && OutputDevice.activePrinter.cameraUrl != null) {
                        cameraImage.start();
                    }
                } else {
                    if (OutputDevice.activePrinter != null && OutputDevice.activePrinter.cameraUrl != null) {
                        cameraImage.stop();
                    }
                }
            }
            source: {
                if (OutputDevice.activePrinter != null && OutputDevice.activePrinter.cameraUrl != null) {
                    return OutputDevice.activePrinter.cameraUrl;
                }
            }
            width: Math.min(imageWidth === 0 ? 800 * screenScaleFactor : imageWidth, maximumWidth);
            z: 1;
        }
    }
}
