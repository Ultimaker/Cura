import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.3 as UM


Item
{
    property var camera: null

    Rectangle
    {
        anchors.fill:parent
        color: UM.Theme.getColor("viewport_overlay")
        opacity: 0.5
    }

    MouseArea
    {
        anchors.fill: parent
        onClicked: OutputDevice.setActiveCamera(null)
        z: 0
    }

    Button
    {
        id: backButton
        anchors.bottom: cameraImage.top
        anchors.bottomMargin: UM.Theme.getSize("default_margin").width
        anchors.right: cameraImage.right

        // TODO: Hardcoded sizes
        width: 20 * screenScaleFactor
        height: 20 * screenScaleFactor

        onClicked: OutputDevice.setActiveCamera(null)

        style: ButtonStyle
        {
            label: Item
            {
                UM.RecolorImage
                {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: control.width
                    height: control.height
                    sourceSize.width: width
                    sourceSize.height: width
                    source: UM.Theme.getIcon("cross1")
                }
            }
            background: Item {}
        }
    }

    Image
    {
        id: cameraImage
        width: Math.min(sourceSize.width === 0 ? 800 * screenScaleFactor : sourceSize.width, maximumWidth)
        height: Math.round((sourceSize.height === 0 ? 600 * screenScaleFactor : sourceSize.height) * width / sourceSize.width)
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        z: 1
        onVisibleChanged:
        {
            if(visible)
            {
                if(camera != null)
                {
                    camera.start()
                }
            } else
            {
                if(camera != null)
                {
                    camera.stop()
                }
            }
        }

        source:
        {
            if(camera != null && camera.latestImage != null)
            {
                return camera.latestImage;
            }
            return "";
        }
    }

    MouseArea
    {
        anchors.fill: cameraImage
        onClicked:
        {
            OutputDevice.setActiveCamera(null)
        }
        z: 1
    }
}
