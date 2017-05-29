import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

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
        //anchors.verticalCenter: parent.verticalCenter
        //anchors.horizontalCenterOffset: - UM.Theme.getSize("sidebar").width / 2
        //visible: base.monitoringPrint
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