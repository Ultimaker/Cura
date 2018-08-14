import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.3 as UM


Item
{
    property var printJob: null

    function getPrettyTime(time)
    {
        return OutputDevice.formatDuration(time)
    }

    Rectangle
    {
        id: background
        anchors.fill: parent

        Item
        {
            // Content on the left of the infobox
            anchors
            {
                top: parent.top
                bottom: parent.bottom
                left: parent.left
                right: parent.horizontalCenter
                margins:  UM.Theme.getSize("default_margin").width
            }

            Label
            {
                id: printJobName
                text: "printJobName"
            }

            Label
            {
                id: ownerName
                anchors.top: printJobName.bottom
                text: "OwnerName"
            }

            Label
            {
                id: totalTimeLabel

                anchors.bottom: parent.bottom
                anchors.right: parent.right

                text: printJob != null ? getPrettyTime(printJob.timeTotal) : "3h 12m"
                elide: Text.ElideRight
            }
        }

        Item
        {
            // Content on the right side of the infobox.
            anchors
            {
                top: parent.top
                bottom: parent.bottom
                left: parent.horizontalCenter
                right: parent.right
                margins:  UM.Theme.getSize("default_margin").width
            }

            Label
            {
                id: targetPrinterLabel
                text: "Waiting for: first available"
            }

            Button
            {
                text: "..."
                anchors
                {
                    right: parent.right
                    top: parent.top
                }
            }

            // PrintCore && Material config
            Row
            {
                id: extruderInfo
                anchors.bottom: parent.bottom

                anchors
                {
                    left: parent.left
                    right: parent.right
                }
                height: childrenRect.height

                spacing: UM.Theme.getSize("default_margin").width

                PrintCoreConfiguration
                {
                    id: leftExtruderInfo
                    width: Math.round((parent.width - extruderSeperator.width) / 2)
                    printCoreConfiguration: printJob.configuration.extruderConfigurations[0]
                }

                Rectangle
                {
                    id: extruderSeperator
                    width: UM.Theme.getSize("default_lining").width
                    height: parent.height
                    color: lineColor
                }

                PrintCoreConfiguration
                {
                    id: rightExtruderInfo
                    width: Math.round((parent.width - extruderSeperator.width) / 2)
                    printCoreConfiguration: printJob.configuration.extruderConfigurations[1]
                }
            }

        }

        Rectangle
        {
            color: "grey"
            width: 1

            anchors.top: parent.top
            anchors.bottom: parent.bottom
            anchors.margins: UM.Theme.getSize("default_margin").height
            anchors.horizontalCenter: parent.horizontalCenter

        }

    }
}