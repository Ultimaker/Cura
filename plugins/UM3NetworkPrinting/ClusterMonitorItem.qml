import QtQuick 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.3 as UM
import Cura 1.0 as Cura

Component
{
    Rectangle
    {
        id: monitorFrame
        width: maximumWidth
        height: maximumHeight
        color: UM.Theme.getColor("viewport_background")
        property var emphasisColor: UM.Theme.getColor("setting_control_border_highlight")
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

            anchors
            {
                top: parent.top
                topMargin: UM.Theme.getSize("default_margin").height * 2 // a bit more spacing to give it some breathing room
                horizontalCenter: parent.horizontalCenter
            }

            text: OutputDevice.printers.length == 0 ? catalog.i18nc("@label: arg 1 is group name", "%1 is not set up to host a group of connected Ultimaker 3 printers").arg(Cura.MachineManager.printerOutputDevices[0].name) : ""

            visible: OutputDevice.printers.length == 0
        }

        Item
        {
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter

            width: Math.min(800 * screenScaleFactor, maximumWidth)
            height: children.height
            visible: OutputDevice.printers.length != 0

            Label
            {
                id: addRemovePrintersLabel
                anchors.right: parent.right
                text: catalog.i18nc("@label link to connect manager", "Add/Remove printers")
                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                linkColor: UM.Theme.getColor("text_link")
            }

            MouseArea
            {
                anchors.fill: addRemovePrintersLabel
                hoverEnabled: true
                onClicked: Cura.MachineManager.printerOutputDevices[0].openPrinterControlPanel()
                onEntered: addRemovePrintersLabel.font.underline = true
                onExited: addRemovePrintersLabel.font.underline = false
            }
        }

        ScrollView
        {
            id: queuedPrintJobs

            anchors
            {
                margins: UM.Theme.getSize("default_margin").width
                top: activePrintersLabel.bottom
                left: parent.left
                bottomMargin: 0
                right: parent.right
                bottom: parent.bottom
            }
            style: UM.Theme.styles.scrollview

            ListView
            {
                anchors.fill: parent
                anchors.margins: UM.Theme.getSize("default_margin").height
                spacing: UM.Theme.getSize("default_margin").height

                model: OutputDevice.queuedPrintJobs

                delegate: PrintJobInfoBlock
                {
                    printJob: modelData
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("default_margin").height
                    height: 175 * screenScaleFactor
                }
            }
        }

        PrinterVideoStream
        {
            visible: OutputDevice.activePrinter != null
            anchors.fill: parent
        }

        onVisibleChanged:
        {
            if (!monitorFrame.visible)
            {
                // After switching the Tab ensure that active printer is Null, the video stream image
                // might be active
                OutputDevice.setActivePrinter(null)
            }
        }
    }
}
