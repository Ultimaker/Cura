import QtQuick 2.2


import UM 1.3 as UM
import Cura 1.0 as Cura

Component
{
    Image
    {
        id: cameraImage
        property bool proportionalHeight:
        {
            if(sourceSize.height == 0 || maximumHeight == 0)
            {
                return true;
            }
            return (sourceSize.width / sourceSize.height) > (maximumWidth / maximumHeight);
        }
        property real _width: Math.floor(Math.min(maximumWidth, sourceSize.width))
        property real _height: Math.floor(Math.min(maximumHeight, sourceSize.height))
        width: proportionalHeight ? _width : Math.floor(sourceSize.width * _height / sourceSize.height)
        height: !proportionalHeight ? _height : Math.floor(sourceSize.height * _width / sourceSize.width)
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