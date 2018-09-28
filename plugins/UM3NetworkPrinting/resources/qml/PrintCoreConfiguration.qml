import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM


Item
{
    id: extruderInfo
    property var printCoreConfiguration

    width: Math.round(parent.width / 2)
    height: childrenRect.height

    Item
    {
        id: extruderCircle
        width: 30
        height: 30

        anchors.verticalCenter: printAndMaterialLabel.verticalCenter
        opacity:
        {
            if(printCoreConfiguration == null || printCoreConfiguration.activeMaterial == null || printCoreConfiguration.hotendID == null)
            {
                return 0.5
            }
            return 1
        }

        Rectangle
        {
            anchors.fill: parent
            radius: Math.round(width / 2)
            border.width: 2
            border.color: "black"
        }

        Label
        {
            anchors.centerIn: parent
            font: UM.Theme.getFont("default_bold")
            text:  printCoreConfiguration.position + 1
        }
    }

    Item
    {
        id: printAndMaterialLabel
        anchors
        {
            right: parent.right
            left: extruderCircle.right
            margins: UM.Theme.getSize("default_margin").width
        }
        height: childrenRect.height

        Label
        {
            id: materialLabel
            text:
            {
                if(printCoreConfiguration != undefined && printCoreConfiguration.activeMaterial != undefined)
                {
                    return printCoreConfiguration.activeMaterial.name
                }
                return ""
            }
            font: UM.Theme.getFont("default_bold")
            elide: Text.ElideRight
            width: parent.width
        }

        Label
        {
            id: printCoreLabel
            text:
            {
                if(printCoreConfiguration != undefined && printCoreConfiguration.hotendID != undefined)
                {
                    return printCoreConfiguration.hotendID
                }
                return ""
            }
            anchors.top: materialLabel.bottom
            elide: Text.ElideRight
            width: parent.width
            opacity: 0.6
            font: UM.Theme.getFont("default")
        }
    }
}
