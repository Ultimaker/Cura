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
    property int leveling_state: 0
    property bool three_point_leveling: true
    property int platform_width: UM.MachineManager.getSettingValue("machine_width")
    property int platform_height: UM.MachineManager.getSettingValue("machine_depth")
    anchors.fill: parent;
    property variant printer_connection: UM.USBPrinterManager.connectedPrinterList.getItem(0).printer
    Component.onCompleted: printer_connection.homeHead()
    Label
    {
        text: ""
        //Component.onCompleted:console.log(UM.Models.settingsModel.getMachineSetting("machine_width"))
    }
    Button
    {
        text: "Move to next position"
        onClicked:
        {
            if(wizardPage.leveling_state == 0)
            {
                printer_connection.moveHead(platform_width /2 , platform_height,0)
            }
            if(wizardPage.leveling_state == 1)
            {
                printer_connection.moveHead(platform_width , 0,0)
            }
            if(wizardPage.leveling_state == 2)
            {
                printer_connection.moveHead(0, 0 ,0)
            }

            wizardPage.leveling_state++

        }
    }

    function threePointLeveling(width, height)
    {
    }


}
