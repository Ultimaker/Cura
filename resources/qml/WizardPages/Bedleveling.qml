// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM
import Cura 1.0 as Cura
import ".."

Item
{
    id: wizardPage
    property int leveling_state: 0
    property bool three_point_leveling: true
    property int platform_width: UM.MachineManager.getSettingValue("machine_width")
    property int platform_height: UM.MachineManager.getSettingValue("machine_depth")
    anchors.fill: parent;
    property variant printer_connection: UM.USBPrinterManager.connectedPrinterList.getItem(0).printer
    Component.onCompleted:
    {
        printer_connection.homeBed()
        printer_connection.moveHeadRelative(0, 0, 3)
        printer_connection.homeHead()
    }
    UM.I18nCatalog { id: catalog; name:"cura"}
    property variant wizard: null;

    Connections
    {
        target: wizardPage.wizard
        onNextClicked: //You can add functions here that get triggered when the final button is clicked in the wizard-element
        {
            if(wizardPage.wizard.lastPage ==  true){
                wizardPage.wizard.visible = false
            }
        }
    }

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
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label","To make sure your prints will come out great, you can now adjust your buildplate. When you click 'Move to Next Position' the nozzle will move to the different positions that can be adjusted.")
    }
    Label
    {
        id: bedlevelingText
        anchors.top: pageDescription.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label", "For every postition; insert a piece of paper under the nozzle and adjust the print bed height. The print bed height is right when the paper is slightly gripped by the tip of the nozzle.")
    }

    Item{
        id: bedlevelingWrapper
        anchors.top: bedlevelingText.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.horizontalCenter: parent.horizontalCenter
        height: skipBedlevelingButton.height
        width: bedlevelingButton.width + skipBedlevelingButton.width + UM.Theme.getSize("default_margin").height < wizardPage.width ? bedlevelingButton.width + skipBedlevelingButton.width + UM.Theme.getSize("default_margin").height : wizardPage.width
        Button
        {
            id: bedlevelingButton
            anchors.top: parent.top
            anchors.left: parent.left
            text: catalog.i18nc("@action:button","Move to Next Position");
            onClicked:
            {
                if(wizardPage.leveling_state == 0)
                {
                    printer_connection.moveHeadRelative(0, 0, 3)
                    printer_connection.homeHead()
                    printer_connection.moveHeadRelative(0, 0, 3)
                    printer_connection.moveHeadRelative(platform_width - 10, 0, 0)
                    printer_connection.moveHeadRelative(0, 0, -3)
                }
                if(wizardPage.leveling_state == 1)
                {
                    printer_connection.moveHeadRelative(0, 0, 3)
                    printer_connection.moveHeadRelative(-platform_width/2, platform_height - 10, 0)
                    printer_connection.moveHeadRelative(0, 0, -3)
                }
                if(wizardPage.leveling_state == 2)
                {
                    printer_connection.moveHeadRelative(0, 0, 3)
                    printer_connection.moveHeadRelative(-platform_width/2 + 10, -(platform_height + 10), 0)
                    printer_connection.moveHeadRelative(0, 0, -3)
                }
                wizardPage.leveling_state++
                if (wizardPage.leveling_state >= 3){
                    resultText.visible = true
                    skipBedlevelingButton.enabled = false
                    bedlevelingButton.enabled = false
                    wizardPage.leveling_state = 0
                }
            }
        }

        Button
        {
            id: skipBedlevelingButton
            anchors.top: parent.width < wizardPage.width ? parent.top : bedlevelingButton.bottom
            anchors.topMargin: parent.width < wizardPage.width ? 0 : UM.Theme.getSize("default_margin").height/2
            anchors.left: parent.width < wizardPage.width ? bedlevelingButton.right : parent.left
            anchors.leftMargin: parent.width < wizardPage.width ? UM.Theme.getSize("default_margin").width : 0
            text: catalog.i18nc("@action:button","Skip Bedleveling");
            onClicked: {
                if(wizardPage.wizard.lastPage ==  true){
                    var old_page_count = wizardPage.wizard.getPageCount()
                    // Delete old pages (if any)
                    for (var i = old_page_count - 1; i > 0; i--)
                    {
                        wizardPage.wizard.removePage(i)
                    }
                    wizardPage.wizard.currentPage = 0
                    wizardPage.wizard.visible = false
                }
            }
        }
    }

    Label
    {
        id: resultText
        visible: false
        anchors.top: bedlevelingWrapper.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.left: parent.left
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label", "Everything is in order! You're done with bedleveling.")
    }

    function threePointLeveling(width, height)
    {

    }
}
