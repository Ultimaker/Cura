import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.3 as UM
import Cura 1.0 as Cura

Component
{
    Rectangle
    {
        width: maximumWidth
        height: maximumHeight
        color: "#FFFFFF" // TODO; Should not be hardcoded.

        property var emphasisColor: "#44c0ff" //TODO: should be linked to theme.
        property var lineColor: "#DCDCDC" // TODO: Should be linked to theme.
        property var cornerRadius: 4 * screenScaleFactor // TODO: Should be linked to theme.
        UM.I18nCatalog
        {
            id: catalog
            name: "cura"
        }

        Label
        {
            id: activePrintersLabel
            font: UM.Theme.getFont("large")

            text:
            {
                if (OutputDevice.connectedPrinters.length == 0){
                    return catalog.i18nc("@label: arg 1 is group name", "%1 is not set up to host a group of connected Ultimaker 3 printers").arg(Cura.MachineManager.printerOutputDevices[0].name)
                } else {
                    return ""
                }
            }
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.topMargin: UM.Theme.getSize("default_margin").height

            visible: OutputDevice.connectedPrinters.length == 0
        }

        Item
        {
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            
            width: Math.min(800 * screenScaleFactor, maximumWidth)
            height: children.height
            visible: OutputDevice.connectedPrinters.length != 0

            Label
            {
                id: addRemovePrintersLabel
                anchors.right: parent.right
                text: "Add / remove printers"
            }

            MouseArea
            {
                anchors.fill: addRemovePrintersLabel
                onClicked: Cura.MachineManager.printerOutputDevices[0].openPrinterControlPanel()
            }
        }


        ScrollView
        {
            id: printerScrollView
            anchors.margins: UM.Theme.getSize("default_margin").width
            anchors.top: activePrintersLabel.bottom
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.leftMargin: UM.Theme.getSize("default_lining").width // To ensure border can be drawn.
            anchors.rightMargin: UM.Theme.getSize("default_lining").width
            anchors.right: parent.right

            ListView
            {
                anchors.fill: parent
                spacing: -UM.Theme.getSize("default_lining").height

                model: OutputDevice.connectedPrinters

                delegate: PrinterInfoBlock
                {
                    printer: modelData
                    width: Math.min(800 * screenScaleFactor, maximumWidth)
                    height: 125 * screenScaleFactor

                    // Add a 1 pix margin, as the border is sometimes cut off otherwise.
                    anchors.horizontalCenter: parent.horizontalCenter
                }
            }
        }

        PrinterVideoStream
        {
            visible: OutputDevice.selectedPrinterName != ""
            anchors.fill:parent
        }
    }
}
