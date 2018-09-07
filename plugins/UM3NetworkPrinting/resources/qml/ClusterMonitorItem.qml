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
            id: manageQueueLabel
            anchors.rightMargin: 4 * UM.Theme.getSize("default_margin").width
            anchors.right: queuedPrintJobs.right
            anchors.bottom: queuedLabel.bottom
            text: catalog.i18nc("@label link to connect manager", "Manage queue")
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("primary")
            linkColor: UM.Theme.getColor("primary")
        }

        MouseArea
        {
            anchors.fill: manageQueueLabel
            hoverEnabled: true
            onClicked: Cura.MachineManager.printerOutputDevices[0].openPrintJobControlPanel()
            onEntered: manageQueueLabel.font.underline = true
            onExited: manageQueueLabel.font.underline = false
        }

        Label
        {
            id: queuedLabel
            anchors.left: queuedPrintJobs.left
            anchors.top: parent.top
            anchors.topMargin: 2 * UM.Theme.getSize("default_margin").height
            anchors.leftMargin: 3 * UM.Theme.getSize("default_margin").width
            text: catalog.i18nc("@label", "Queued")
            font: UM.Theme.getFont("large")
            color: UM.Theme.getColor("text")
        }

        ScrollView
        {
            id: queuedPrintJobs

            anchors
            {
                top: queuedLabel.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                horizontalCenter: parent.horizontalCenter
                bottomMargin: 0
                bottom: parent.bottom
            }
            style: UM.Theme.styles.scrollview
            width: Math.min(800 * screenScaleFactor, maximumWidth)
            ListView
            {
                anchors.fill: parent
                //anchors.margins: UM.Theme.getSize("default_margin").height
                spacing: UM.Theme.getSize("default_margin").height - 10 // 2x the shadow radius

                model: OutputDevice.queuedPrintJobs

                delegate: PrintJobInfoBlock
                {
                    printJob: modelData
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("default_margin").height
                    anchors.leftMargin: UM.Theme.getSize("default_margin").height
                    height: 175 * screenScaleFactor
                }
            }
        }

        PrinterVideoStream
        {
            visible: OutputDevice.activeCamera != null
            anchors.fill: parent
            camera: OutputDevice.activeCamera
        }

        onVisibleChanged:
        {
            if (monitorFrame != null && !monitorFrame.visible)
            {
                OutputDevice.setActiveCamera(null)
            }
        }
    }
}
