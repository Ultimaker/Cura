// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

Item
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
        id: pageTitle
        width: parent.width
        text: catalog.i18nc("@title", "Bed Leveling")
        wrapMode: Text.WordWrap
        font.pointSize: 18;
    }

    Label
    {
        id: pageDescription
        anchors.top: pageTitle.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label","To make sure your prints will come out great, you can now adjust your buildplate. When you click 'Move to Next Position' the nozzle will move to the different positions that can be adjusted.")
    }
    Label
    {
        id: bedelevelingText
        anchors.top: pageDescription.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label", "For every postition; insert a piece of paper under the nozzle and adjust the print bed height. The print bed height is right when the paper is slightly gripped by the tip of the nozzle.")
    }

    Item{
        anchors.top: bedelevelingText.bottom
        anchors.topMargin: UM.Theme.sizes.default_margin.height
        anchors.horizontalCenter: parent.horizontalCenter
        width: bedelevelingButton.width + skipBedlevelingButton.width + UM.Theme.sizes.default_margin.height < wizardPage.width ? bedelevelingButton.width + skipBedlevelingButton.width + UM.Theme.sizes.default_margin.height : wizardPage.width
        Button
        {
            id: bedelevelingButton
            anchors.top: parent.top
            anchors.left: parent.left
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
            id: skipBedlevelingButton
            anchors.top: parent.width < wizardPage.width ? parent.top : bedelevelingButton.bottom
            anchors.topMargin: parent.width < wizardPage.width ? 0 : UM.Theme.sizes.default_margin.height/2
            anchors.left: parent.width < wizardPage.width ? bedelevelingButton.right : parent.left
            anchors.leftMargin: parent.width < wizardPage.width ? UM.Theme.sizes.default_margin.width : 0
            text: catalog.i18nc("@action:button","Skip Bedleveling");
            onClicked: base.visible = false;
        }
    }

    function threePointLeveling(width, height)
    {

    }
}
