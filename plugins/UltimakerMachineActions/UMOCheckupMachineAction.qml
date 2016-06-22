import UM 1.2 as UM
import Cura 1.0 as Cura

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

Cura.MachineAction
{
    anchors.fill: parent;
    Item
    {
        id: checkupMachineAction
        anchors.fill: parent;
        property int leftRow: checkupMachineAction.width * 0.40
        property int rightRow: checkupMachineAction.width * 0.60
        UM.I18nCatalog { id: catalog; name:"cura"}
        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Check Printer")
            wrapMode: Text.WordWrap
            font.pointSize: 18;
        }

        Label
        {
            id: pageDescription
            anchors.top: pageTitle.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label","It's a good idea to do a few sanity checks on your Ultimaker. You can skip this step if you know your machine is functional");
        }

        Item
        {
            id: startStopButtons
            anchors.top: pageDescription.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.horizontalCenter: parent.horizontalCenter
            height: childrenRect.height
            width: startCheckButton.width + skipCheckButton.width + UM.Theme.getSize("default_margin").height < checkupMachineAction.width ? startCheckButton.width + skipCheckButton.width + UM.Theme.getSize("default_margin").height : checkupMachineAction.width
            Button
            {
                id: startCheckButton
                anchors.top: parent.top
                anchors.left: parent.left
                text: catalog.i18nc("@action:button","Start Printer Check");
                onClicked:
                {
                    checkupContent.visible = true
                    startCheckButton.enabled = false
                    manager.startCheck()
                }
            }

            Button
            {
                id: skipCheckButton
                anchors.top: parent.width < checkupMachineAction.width ? parent.top : startCheckButton.bottom
                anchors.topMargin: parent.width < checkupMachineAction.width ? 0 : UM.Theme.getSize("default_margin").height/2
                anchors.left: parent.width < checkupMachineAction.width ? startCheckButton.right : parent.left
                anchors.leftMargin: parent.width < checkupMachineAction.width ? UM.Theme.getSize("default_margin").width : 0
                text: catalog.i18nc("@action:button", "Skip Printer Check");
                onClicked: manager.setFinished()
            }
        }

        Item
        {
            id: checkupContent
            anchors.top: startStopButtons.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            visible: false
            width: parent.width
            height: 250
            //////////////////////////////////////////////////////////
            Label
            {
                id: connectionLabel
                width: checkupMachineAction.leftRow
                anchors.left: parent.left
                anchors.top: parent.top
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","Connection: ")
            }
            Label
            {
                id: connectionStatus
                width: checkupMachineAction.rightRow
                anchors.left: connectionLabel.right
                anchors.top: parent.top
                wrapMode: Text.WordWrap
                text: Cura.USBPrinterManager.connectedPrinterList.rowCount() > 0 || base.addOriginalProgress.checkUp[0] ? catalog.i18nc("@info:status","Done"):catalog.i18nc("@info:status","Incomplete")
            }
            //////////////////////////////////////////////////////////
            Label
            {
                id: endstopXLabel
                width: checkupMachineAction.leftRow
                anchors.left: parent.left
                anchors.top: connectionLabel.bottom
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","Min endstop X: ")
            }
            Label
            {
                id: endstopXStatus
                width: checkupMachineAction.rightRow
                anchors.left: endstopXLabel.right
                anchors.top: connectionLabel.bottom
                wrapMode: Text.WordWrap
                text: manager.xMinEndstopTestCompleted ? catalog.i18nc("@info:status","Works") : catalog.i18nc("@info:status","Not checked")
            }
            //////////////////////////////////////////////////////////////
            Label
            {
                id: endstopYLabel
                width: checkupMachineAction.leftRow
                anchors.left: parent.left
                anchors.top: endstopXLabel.bottom
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","Min endstop Y: ")
            }
            Label
            {
                id: endstopYStatus
                width: checkupMachineAction.rightRow
                anchors.left: endstopYLabel.right
                anchors.top: endstopXLabel.bottom
                wrapMode: Text.WordWrap
                text: manager.yMinEndstopTestCompleted ? catalog.i18nc("@info:status","Works") : catalog.i18nc("@info:status","Not checked")
            }
            /////////////////////////////////////////////////////////////////////
            Label
            {
                id: endstopZLabel
                width: checkupMachineAction.leftRow
                anchors.left: parent.left
                anchors.top: endstopYLabel.bottom
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","Min endstop Z: ")
            }
            Label
            {
                id: endstopZStatus
                width: checkupMachineAction.rightRow
                anchors.left: endstopZLabel.right
                anchors.top: endstopYLabel.bottom
                wrapMode: Text.WordWrap
                text: manager.zMinEndstopTestCompleted ? catalog.i18nc("@info:status","Works") : catalog.i18nc("@info:status","Not checked")
            }
            ////////////////////////////////////////////////////////////
            Label
            {
                id: nozzleTempLabel
                width: checkupMachineAction.leftRow
                anchors.left: parent.left
                anchors.top: endstopZLabel.bottom
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","Nozzle temperature check: ")
            }
            Label
            {
                id: nozzleTempStatus
                width: checkupMachineAction.rightRow * 0.4
                anchors.top: nozzleTempLabel.top
                anchors.left: nozzleTempLabel.right
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@info:status","Not checked")
            }
            Item
            {
                id: nozzleTempButton
                width: checkupMachineAction.rightRow * 0.3
                height: nozzleTemp.height
                anchors.top: nozzleTempLabel.top
                anchors.left: bedTempStatus.right
                anchors.leftMargin: UM.Theme.getSize("default_margin").width/2
                Button
                {
                    height: nozzleTemp.height - 2
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: catalog.i18nc("@action:button","Start Heating")
                    onClicked:
                    {
                        manager.heatupHotend()
                        nozzleTempStatus.text = catalog.i18nc("@info:progress","Checking")
                    }
                }
            }
            Label
            {
                id: nozzleTemp
                anchors.top: nozzleTempLabel.top
                anchors.left: nozzleTempButton.right
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                width: checkupMachineAction.rightRow * 0.2
                wrapMode: Text.WordWrap
                text: manager.hotendTemperature + "°C"
                font.bold: true
            }
            /////////////////////////////////////////////////////////////////////////////
            Label
            {
                id: bedTempLabel
                width: checkupMachineAction.leftRow
                anchors.left: parent.left
                anchors.top: nozzleTempLabel.bottom
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","bed temperature check:")
            }

            Label
            {
                id: bedTempStatus
                width: checkupMachineAction.rightRow * 0.4
                anchors.top: bedTempLabel.top
                anchors.left: bedTempLabel.right
                wrapMode: Text.WordWrap
                text: manager.bedTestCompleted ? catalog.i18nc("@info:status","Not checked"): catalog.i18nc("@info:status","Checked")
            }
            Item
            {
                id: bedTempButton
                width: checkupMachineAction.rightRow * 0.3
                height: bedTemp.height
                anchors.top: bedTempLabel.top
                anchors.left: bedTempStatus.right
                anchors.leftMargin: UM.Theme.getSize("default_margin").width/2
                Button
                {
                    height: bedTemp.height - 2
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: catalog.i18nc("@action:button","Start Heating")
                    onClicked:
                    {
                        manager.heatupBed()
                    }
                }
            }
            Label
            {
                id: bedTemp
                width: checkupMachineAction.rightRow * 0.2
                anchors.top: bedTempLabel.top
                anchors.left: bedTempButton.right
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                wrapMode: Text.WordWrap
                text: manager.bedTemperature + "°C"
                font.bold: true
            }
            Label
            {
                id: resultText
                visible: false
                anchors.top: bedTemp.bottom
                anchors.topMargin: UM.Theme.getSize("default_margin").height
                anchors.left: parent.left
                width: parent.width
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label", "Everything is in order! You're done with your CheckUp.")
            }
        }
    }
}