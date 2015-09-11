// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

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
    UM.I18nCatalog { id: catalog; name:"cura"}

    Label
    {
        text: catalog.i18nc("@title", "Bed Leveling")
        font.pointSize: 18;
    }

    Label
    {
        id: pageDescription
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label","To make sure your prints will come out great, you can now adjust your buildplate. When you click 'Move to Next Position' the nozzle will move to the different positions that can be adjusted.")
    }
    Label
    {
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label", "For every postition; insert a piece of paper under the nozzle and adjust the print bed height. The print bed height is right when the paper is slightly gripped by the tip of the nozzle.")
    }
    Button
    {
        text: catalog.i18nc("@action:button","Move to Next Position");
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

    Button
    {
        text: catalog.i18nc("@action:button","Skip Bedleveling");
    }

    function threePointLeveling(width, height)
    {

    }
}
