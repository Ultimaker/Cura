import QtQuick 2.3
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.3
import QtQuick.Controls 2.0 as Controls2
import QtGraphicalEffects 1.0

import UM 1.3 as UM
import Cura 1.0 as Cura

Rectangle
{
    property var iconSource: null

    width: 36 * screenScaleFactor
    height: width
    radius: 0.5 * width
    color: clickArea.containsMouse ? UM.Theme.getColor("primary_hover") : UM.Theme.getColor("primary")

    UM.RecolorImage
    {
        id: icon
        width: parent.width / 2
        height: width
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
        color: UM.Theme.getColor("primary_text")
        source: iconSource
    }

    MouseArea
    {
        id: clickArea
        anchors.fill:parent
        hoverEnabled: true
        onClicked:
        {
            if (OutputDevice.activeCamera !== null)
            {
                OutputDevice.setActiveCamera(null)
            }
            else
            {
                OutputDevice.setActiveCamera(modelData.camera)
            }
        }
    }
}