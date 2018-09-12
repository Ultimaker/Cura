import QtQuick 2.2


import UM 1.3 as UM
import Cura 1.0 as Cura

Component
{
    Item
    {
        width: maximumWidth
        height: maximumHeight
        Image
        {
            id: cameraImage
            width: Math.min(sourceSize.width === 0 ? 800 * screenScaleFactor : sourceSize.width, maximumWidth)
            height: Math.floor((sourceSize.height === 0 ? 600 * screenScaleFactor : sourceSize.height) * width / sourceSize.width)
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter
            z: 1
            Component.onCompleted:
            {
                if(OutputDevice.activePrinter != null && OutputDevice.activePrinter.camera != null)
                {
                    OutputDevice.activePrinter.camera.start()
                }
            }
            onVisibleChanged:
            {
                if(visible)
                {
                    if(OutputDevice.activePrinter != null && OutputDevice.activePrinter.camera != null)
                    {
                        OutputDevice.activePrinter.camera.start()
                    }
                } else
                {
                    if(OutputDevice.activePrinter != null && OutputDevice.activePrinter.camera != null)
                    {
                        OutputDevice.activePrinter.camera.stop()
                    }
                }
            }
            source:
            {
                if(OutputDevice.activePrinter != null && OutputDevice.activePrinter.camera != null && OutputDevice.activePrinter.camera.latestImage)
                {
                    return OutputDevice.activePrinter.camera.latestImage;
                }
                return "";
            }
        }
    }
}