// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

Column
{
    id: wizardPage
    property string title
    anchors.fill: parent;
    property bool x_min_pressed: false
    property bool y_min_pressed: false
    property bool z_min_pressed: false
    property bool heater_works: false
    property int extruder_target_temp: 0
    property int bed_target_temp: 0
    property variant printer_connection: UM.USBPrinterManager.connectedPrinterList.getItem(0).printer

    Component.onCompleted: printer_connection.startPollEndstop()

    Label
    {
        text: parent.title
        font.pointSize: 18;
    }

    Label
    {
        //: Add Printer wizard page description
        text: qsTr("It's a good idea to do a few sanity checks on your Ultimaker. \n You can skip these if you know your machine is functional");
    }

    Row
    {
        Label
        {
            text: qsTr("Connection: ")
        }
        Label
        {
            text: UM.USBPrinterManager.connectedPrinterList.count ? "Done":"Incomplete"
        }
    }
    Row
    {
        Label
        {
            text: qsTr("Min endstop X: ")
        }
        Label
        {
            text: x_min_pressed ? qsTr("Works") : qsTr("Not checked")
        }
    }
    Row
    {
        Label
        {
            text: qsTr("Min endstop Y: ")
        }
        Label
        {
            text: y_min_pressed ? qsTr("Works") : qsTr("Not checked")
        }
    }

    Row
    {
        Label
        {
            text: qsTr("Min endstop Z: ")
        }
        Label
        {
            text: z_min_pressed ? qsTr("Works") : qsTr("Not checked")
        }
    }

    Row
    {
        Label
        {
            text: qsTr("Nozzle temperature check: ")
        }
        Label
        {
            text: printer_connection.extruderTemperature
        }
        Button
        {
            text: "Start heating"
            onClicked:
            {
                heater_status_label.text = qsTr("Checking")
                printer_connection.heatupNozzle(190)
                wizardPage.extruder_target_temp = 190
            }
        }
        Label
        {
            id: heater_status_label
            text: qsTr("Not checked")
        }
    }

    Row
    {
        Label
        {
            text: qsTr("bed temperature check: ")
        }
        Label
        {
            text: printer_connection.bedTemperature
        }
        Button
        {
            text: "Start heating"
            onClicked:
            {
                bed_status_label.text = qsTr("Checking")
                printer_connection.printer.heatupBed(60)
                wizardPage.bed_target_temp = 60
            }
        }
        Label
        {
            id: bed_status_label
            text: qsTr("Not checked")
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
            }
            if(key == "y_min")
            {
                y_min_pressed = true
            }
            if(key == "z_min")
            {
                z_min_pressed = true
            }
        }
        onExtruderTemperatureChanged:
        {
            if(printer_connection.extruderTemperature > wizardPage.extruder_target_temp - 10 && printer_connection.extruderTemperature < wizardPage.extruder_target_temp + 10)
            {
                heater_status_label.text = qsTr("Works")
                printer_connection.heatupNozzle(0)
            }
        }
        onBedTemperatureChanged:
        {
            if(printer_connection.bedTemperature > wizardPage.bed_target_temp - 5 && printer_connection.bedTemperature < wizardPage.bed_target_temp + 5)
            {
                bed_status_label.text = qsTr("Works")
                printer_connection.heatupBed(0)
            }
        }
    }

    ExclusiveGroup
    {
        id: printerGroup;
    }
}