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
        property int leftRow: (checkupMachineAction.width * 0.40) | 0
        property int rightRow: (checkupMachineAction.width * 0.60) | 0
        property bool heatupHotendStarted: false
        property bool heatupBedStarted: false
        property bool printerConnected: Cura.MachineManager.printerConnected

        UM.I18nCatalog { id: catalog; name: "cura"}
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
            text: catalog.i18nc("@label", "It's a good idea to do a few sanity checks on your Ultimaker. You can skip this step if you know your machine is functional");
        }

        Row
        {
            id: startStopButtons
            anchors.top: pageDescription.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            anchors.horizontalCenter: parent.horizontalCenter
            width: childrenRect.width
            spacing: UM.Theme.getSize("default_margin").width
            Button
            {
                id: startCheckButton
                text: catalog.i18nc("@action:button","Start Printer Check");
                onClicked:
                {
                    checkupMachineAction.heatupHotendStarted = false;
                    checkupMachineAction.heatupBedStarted = false;
                    manager.startCheck();
                    startCheckButton.visible = false;
                }
            }
        }

        Item
        {
            id: checkupContent
            anchors.top: startStopButtons.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
            visible: manager.checkStarted
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
                text: checkupMachineAction.printerConnected ? catalog.i18nc("@info:status","Connected"): catalog.i18nc("@info:status","Not connected")
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
                visible: checkupMachineAction.printerConnected
            }
            Label
            {
                id: endstopXStatus
                width: checkupMachineAction.rightRow
                anchors.left: endstopXLabel.right
                anchors.top: connectionLabel.bottom
                wrapMode: Text.WordWrap
                text: manager.xMinEndstopTestCompleted ? catalog.i18nc("@info:status","Works") : catalog.i18nc("@info:status","Not checked")
                visible: checkupMachineAction.printerConnected
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
                visible: checkupMachineAction.printerConnected
            }
            Label
            {
                id: endstopYStatus
                width: checkupMachineAction.rightRow
                anchors.left: endstopYLabel.right
                anchors.top: endstopXLabel.bottom
                wrapMode: Text.WordWrap
                text: manager.yMinEndstopTestCompleted ? catalog.i18nc("@info:status","Works") : catalog.i18nc("@info:status","Not checked")
                visible: checkupMachineAction.printerConnected
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
                visible: checkupMachineAction.printerConnected
            }
            Label
            {
                id: endstopZStatus
                width: checkupMachineAction.rightRow
                anchors.left: endstopZLabel.right
                anchors.top: endstopYLabel.bottom
                wrapMode: Text.WordWrap
                text: manager.zMinEndstopTestCompleted ? catalog.i18nc("@info:status","Works") : catalog.i18nc("@info:status","Not checked")
                visible: checkupMachineAction.printerConnected
            }
            ////////////////////////////////////////////////////////////
            Label
            {
                id: nozzleTempLabel
                width: checkupMachineAction.leftRow
                height: nozzleTempButton.height
                anchors.left: parent.left
                anchors.top: endstopZLabel.bottom
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","Nozzle temperature check: ")
                visible: checkupMachineAction.printerConnected
            }
            Label
            {
                id: nozzleTempStatus
                width: (checkupMachineAction.rightRow * 0.4) | 0
                anchors.top: nozzleTempLabel.top
                anchors.left: nozzleTempLabel.right
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@info:status","Not checked")
                visible: checkupMachineAction.printerConnected
            }
            Item
            {
                id: nozzleTempButton
                width: (checkupMachineAction.rightRow * 0.3) | 0
                height: childrenRect.height
                anchors.top: nozzleTempLabel.top
                anchors.left: bedTempStatus.right
                anchors.leftMargin: Math.round(UM.Theme.getSize("default_margin").width/2)
                visible: checkupMachineAction.printerConnected
                Button
                {
                    text: checkupMachineAction.heatupHotendStarted ? catalog.i18nc("@action:button","Stop Heating") : catalog.i18nc("@action:button","Start Heating")
                    onClicked:
                    {
                        if (checkupMachineAction.heatupHotendStarted)
                        {
                            manager.cooldownHotend()
                            checkupMachineAction.heatupHotendStarted = false
                        } else
                        {
                            manager.heatupHotend()
                            checkupMachineAction.heatupHotendStarted = true
                        }
                    }
                }
            }
            Label
            {
                id: nozzleTemp
                anchors.top: nozzleTempLabel.top
                anchors.left: nozzleTempButton.right
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                width: (checkupMachineAction.rightRow * 0.2) | 0
                wrapMode: Text.WordWrap
                text: manager.hotendTemperature + "°C"
                font.bold: true
                visible: checkupMachineAction.printerConnected
            }
            /////////////////////////////////////////////////////////////////////////////
            Label
            {
                id: bedTempLabel
                width: checkupMachineAction.leftRow
                height: bedTempButton.height
                anchors.left: parent.left
                anchors.top: nozzleTempLabel.bottom
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label","Build plate temperature check:")
                visible: checkupMachineAction.printerConnected && manager.hasHeatedBed
            }

            Label
            {
                id: bedTempStatus
                width: (checkupMachineAction.rightRow * 0.4) | 0
                anchors.top: bedTempLabel.top
                anchors.left: bedTempLabel.right
                wrapMode: Text.WordWrap
                text: manager.bedTestCompleted ? catalog.i18nc("@info:status","Not checked"): catalog.i18nc("@info:status","Checked")
                visible: checkupMachineAction.printerConnected && manager.hasHeatedBed
            }
            Item
            {
                id: bedTempButton
                width: (checkupMachineAction.rightRow * 0.3) | 0
                height: childrenRect.height
                anchors.top: bedTempLabel.top
                anchors.left: bedTempStatus.right
                anchors.leftMargin: Math.round(UM.Theme.getSize("default_margin").width/2)
                visible: checkupMachineAction.printerConnected && manager.hasHeatedBed
                Button
                {
                    text: checkupMachineAction.heatupBedStarted ?catalog.i18nc("@action:button","Stop Heating") : catalog.i18nc("@action:button","Start Heating")
                    onClicked:
                    {
                        if (checkupMachineAction.heatupBedStarted)
                        {
                            manager.cooldownBed()
                            checkupMachineAction.heatupBedStarted = false
                        } else
                        {
                            manager.heatupBed()
                            checkupMachineAction.heatupBedStarted = true
                        }
                    }
                }
            }
            Label
            {
                id: bedTemp
                width: (checkupMachineAction.rightRow * 0.2) | 0
                anchors.top: bedTempLabel.top
                anchors.left: bedTempButton.right
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
                wrapMode: Text.WordWrap
                text: manager.bedTemperature + "°C"
                font.bold: true
                visible: checkupMachineAction.printerConnected && manager.hasHeatedBed
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