import QtQuick 2.2


import UM 1.3 as UM
import Cura 1.0 as Cura

Component
{
    Image
    {
        id: cameraImage
        width: sourceSize.width
        height: sourceSize.height * width / sourceSize.width
        anchors.horizontalCenter: parent.horizontalCenter
        onVisibleChanged:
        {
            if(visible)
            {
                OutputDevice.startCamera()
            } else
            {
                OutputDevice.stopCamera()
            }
        }
        source:
        {
            if(OutputDevice.cameraImage)
            {
                return OutputDevice.cameraImage;
            }
            return "";
        }
    }
}