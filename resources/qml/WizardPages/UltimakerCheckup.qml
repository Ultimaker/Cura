// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

Item
{
    id: wizardPage
    property string title
    property int leftRow: wizardPage.width*0.40
    property int rightRow: wizardPage.width*0.60
    anchors.fill: parent;
    property bool x_min_pressed: false
    property bool y_min_pressed: false
    property bool z_min_pressed: false
    property bool heater_works: false
    property int extruder_target_temp: 0
    property int bed_target_temp: 0
    UM.I18nCatalog { id: catalog; name:"cura"}
    property var checkupProgress: {
        "connection": false,
        "endstopX": wizardPage.x_min_pressed,
        "endstopY": wizardPage.y_min_pressed,
        "endstopZ": wizardPage.z_min_pressed,
        "nozzleTemp": false,
        "bedTemp": false
    }

    property variant printer_connection: {
        if (UM.USBPrinterManager.connectedPrinterList.rowCount() != 0){
            wizardPage.checkupProgress.connection = true
            return UM.USBPrinterManager.connectedPrinterList.getItem(0).printer
        }
        else {
            return null
        }
    }

    function checkTotalCheckUp(){
        var allDone = true
        for(var property in checkupProgress){
            if (checkupProgress[property] == false){
                allDone = false
            }
        }
        if (allDone == true){
            skipCheckButton.enabled = false
            resultText.visible = true
        }
    }

    Component.onCompleted:
    {
        if (printer_connection != null){
            printer_connection.startPollEndstop()
        }
    }
    Component.onDestruction:
    {
        if (printer_connection != null){
            printer_connection.stopPollEndstop()
        }
    }
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

    Item{
        id: startStopButtons
        anchors.top: pageDescription.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.horizontalCenter: parent.horizontalCenter
        height: childrenRect.height
        width: startCheckButton.width + skipCheckButton.width + UM.Theme.getSize("default_margin").height < wizardPage.width ? startCheckButton.width + skipCheckButton.width + UM.Theme.getSize("default_margin").height : wizardPage.width
        Button
        {
            id: startCheckButton
            anchors.top: parent.top
            anchors.left: parent.left
            //enabled: !alreadyTested
            text: catalog.i18nc("@action:button","Start Printer Check");
            onClicked: {
                checkupContent.visible = true
                startCheckButton.enabled = false
                printer_connection.homeHead()
            }
        }

        Button
        {
            id: skipCheckButton
            anchors.top: parent.width < wizardPage.width ? parent.top : startCheckButton.bottom
            anchors.topMargin: parent.width < wizardPage.width ? 0 : UM.Theme.getSize("default_margin").height/2
            anchors.left: parent.width < wizardPage.width ? startCheckButton.right : parent.left
            anchors.leftMargin: parent.width < wizardPage.width ? UM.Theme.getSize("default_margin").width : 0
            //enabled: !alreadyTested
            text: catalog.i18nc("@action:button","Skip Printer Check");
            onClicked: {
                base.currentPage += 1
            }
        }
    }

    Item{
        id: checkupContent
        anchors.top: startStopButtons.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        visible: false
        //////////////////////////////////////////////////////////
        Label
        {
            id: connectionLabel
            width: wizardPage.leftRow
            anchors.left: parent.left
            anchors.top: parent.top
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label","Connection: ")
        }
        Label
        {
            id: connectionStatus
            width: wizardPage.rightRow
            anchors.left: connectionLabel.right
            anchors.top: parent.top
            wrapMode: Text.WordWrap
            text: UM.USBPrinterManager.connectedPrinterList.rowCount() > 0 || base.addOriginalProgress.checkUp[0] ? catalog.i18nc("@info:status","Done"):catalog.i18nc("@info:status","Incomplete")
        }
        //////////////////////////////////////////////////////////
        Label
        {
            id: endstopXLabel
            width: wizardPage.leftRow
            anchors.left: parent.left
            anchors.top: connectionLabel.bottom
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label","Min endstop X: ")
        }
        Label
        {
            id: endstopXStatus
            width: wizardPage.rightRow
            anchors.left: endstopXLabel.right
            anchors.top: connectionLabel.bottom
            wrapMode: Text.WordWrap
            text: x_min_pressed ? catalog.i18nc("@info:status","Works") : catalog.i18nc("@info:status","Not checked")
        }
        //////////////////////////////////////////////////////////////
        Label
        {
            id: endstopYLabel
            width: wizardPage.leftRow
            anchors.left: parent.left
            anchors.top: endstopXLabel.bottom
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label","Min endstop Y: ")
        }
        Label
        {
            id: endstopYStatus
            width: wizardPage.rightRow
            anchors.left: endstopYLabel.right
            anchors.top: endstopXLabel.bottom
            wrapMode: Text.WordWrap
            text: y_min_pressed ? catalog.i18nc("@info:status","Works") : catalog.i18nc("@info:status","Not checked")
        }
        /////////////////////////////////////////////////////////////////////
        Label
        {
            id: endstopZLabel
            width: wizardPage.leftRow
            anchors.left: parent.left
            anchors.top: endstopYLabel.bottom
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label","Min endstop Z: ")
        }
        Label
        {
            id: endstopZStatus
            width: wizardPage.rightRow
            anchors.left: endstopZLabel.right
            anchors.top: endstopYLabel.bottom
            wrapMode: Text.WordWrap
            text: z_min_pressed ? catalog.i18nc("@info:status","Works") : catalog.i18nc("@info:status","Not checked")
        }
        ////////////////////////////////////////////////////////////
        Label
        {
            id: nozzleTempLabel
            width: wizardPage.leftRow
            anchors.left: parent.left
            anchors.top: endstopZLabel.bottom
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label","Nozzle temperature check: ")
        }
        Label
        {
            id: nozzleTempStatus
            width: wizardPage.rightRow * 0.4
            anchors.top: nozzleTempLabel.top
            anchors.left: nozzleTempLabel.right
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@info:status","Not checked")
        }
        Item
        {
            id: nozzleTempButton
            width: wizardPage.rightRow * 0.3
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
                    if(printer_connection != null)
                    {
                        nozzleTempStatus.text = catalog.i18nc("@info:progress","Checking")
                        printer_connection.heatupNozzle(190)
                        wizardPage.extruder_target_temp = 190
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
            width: wizardPage.rightRow * 0.2
            wrapMode: Text.WordWrap
            text: printer_connection != null ? printer_connection.extruderTemperature + "°C" : "0°C"
            font.bold: true
        }
        /////////////////////////////////////////////////////////////////////////////
        Label
        {
            id: bedTempLabel
            width: wizardPage.leftRow
            anchors.left: parent.left
            anchors.top: nozzleTempLabel.bottom
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label","bed temperature check:")
        }

        Label
        {
            id: bedTempStatus
            width: wizardPage.rightRow * 0.4
            anchors.top: bedTempLabel.top
            anchors.left: bedTempLabel.right
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@info:status","Not checked")
        }
        Item
        {
            id: bedTempButton
            width: wizardPage.rightRow * 0.3
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
                    if(printer_connection != null)
                    {
                        bedTempStatus.text = catalog.i18nc("@info:progress","Checking")
                        printer_connection.heatupBed(60)
                        wizardPage.bed_target_temp = 60
                    }
                }
            }
        }
        Label
        {
            id: bedTemp
            width: wizardPage.rightRow * 0.2
            anchors.top: bedTempLabel.top
            anchors.left: bedTempButton.right
            anchors.leftMargin: UM.Theme.getSize("default_margin").width
            wrapMode: Text.WordWrap
            text: printer_connection != null ? printer_connection.bedTemperature + "°C": "0°C"
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


    Connections
    {
        target: printer_connection
        onEndstopStateChanged:
        {
            if(key == "x_min")
            {
                x_min_pressed = true
                checkTotalCheckUp()
            }
            if(key == "y_min")
            {
                y_min_pressed = true
                checkTotalCheckUp()
            }
            if(key == "z_min")
            {
                z_min_pressed = true
                checkTotalCheckUp()
            }
        }

        onExtruderTemperatureChanged:
        {
            if(printer_connection.extruderTemperature > wizardPage.extruder_target_temp - 10 && printer_connection.extruderTemperature < wizardPage.extruder_target_temp + 10)
            {
                if(printer_connection != null)
                {
                    nozzleTempStatus.text = catalog.i18nc("@info:status","Works")
                    wizardPage.checkupProgress.nozzleTemp = true
                    checkTotalCheckUp()
                    printer_connection.heatupNozzle(0)
                }
            }
        }
        onBedTemperatureChanged:
        {
            if(printer_connection.bedTemperature > wizardPage.bed_target_temp - 5 && printer_connection.bedTemperature < wizardPage.bed_target_temp + 5)
            {
                bedTempStatus.text = catalog.i18nc("@info:status","Works")
                wizardPage.checkupProgress.bedTemp = true
                checkTotalCheckUp()
                printer_connection.heatupBed(0)
            }
        }
    }

    ExclusiveGroup
    {
        id: printerGroup;
    }
}