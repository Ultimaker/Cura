import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.3 as UM


Item
{
    Rectangle
    {
        anchors.fill:parent
        color: UM.Theme.getColor("viewport_overlay")
        opacity: 0.5
    }

    MouseArea
    {
      anchors.fill: parent
      onClicked: OutputDevice.setActivePrinter(null)
      z: 0
    }

    Button
    {
        id: backButton
        anchors.bottom: cameraImage.top
        anchors.bottomMargin: UM.Theme.getSize("default_margin").width
        anchors.right: cameraImage.right

        // TODO: Harcoded sizes
        width: 20 * screenScaleFactor
        height: 20 * screenScaleFactor

        onClicked: OutputDevice.setActivePrinter(null)

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

    MouseArea
    {
      anchors.fill: cameraImage
      onClicked: { /* no-op */ }
      z: 1
    }

}
