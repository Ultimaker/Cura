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

    SystemPalette{id: palette}
    UM.I18nCatalog { id: catalog; name:"cura"}
    property variant printer_connection: UM.USBPrinterManager.connectedPrinterList.rowCount() != 0 ? UM.USBPrinterManager.connectedPrinterList.getItem(0).printer : null
    Label
    {
        id: pageTitle
        width: parent.width
        text: catalog.i18nc("@title", "Upgrade Firmware")
        wrapMode: Text.WordWrap
        font.pointSize: 18
    }
    Label
    {
        id: pageDescription
        anchors.top: pageTitle.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label","Firmware is the piece of software running directly on your 3D printer. This firmware controls the step motors, regulates the temperature and ultimately makes your printer work.")
    }

    Label
    {
        id: upgradeText1
        anchors.top: pageDescription.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label","The firmware shipping with new Ultimakers works, but upgrades have been made to make better prints, and make calibration easier.");
    }

    Label
    {
        id: upgradeText2
        anchors.top: upgradeText1.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        width: parent.width
        wrapMode: Text.WordWrap
        text: catalog.i18nc("@label","Cura requires these new features and thus your firmware will most likely need to be upgraded. You can do so now.");
    }
    Item{
        anchors.top: upgradeText2.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.horizontalCenter: parent.horizontalCenter
        width: upgradeButton.width + skipUpgradeButton.width + UM.Theme.getSize("default_margin").height < wizardPage.width ? upgradeButton.width + skipUpgradeButton.width + UM.Theme.getSize("default_margin").height : wizardPage.width
        Button {
            id: upgradeButton
            anchors.top: parent.top
            anchors.left: parent.left
            text: catalog.i18nc("@action:button","Upgrade to Marlin Firmware");
            onClicked: UM.USBPrinterManager.updateAllFirmware()
        }
        Button {
            id: skipUpgradeButton
            anchors.top: parent.width < wizardPage.width ? parent.top : upgradeButton.bottom
            anchors.topMargin: parent.width < wizardPage.width ? 0 : UM.Theme.getSize("default_margin").height/2
            anchors.left: parent.width < wizardPage.width ? upgradeButton.right : parent.left
            anchors.leftMargin: parent.width < wizardPage.width ? UM.Theme.getSize("default_margin").width : 0
            text: catalog.i18nc("@action:button","Skip Upgrade");
            onClicked: {
                base.currentPage += 1
            }
        }
    }
    ExclusiveGroup { id: printerGroup; }
}