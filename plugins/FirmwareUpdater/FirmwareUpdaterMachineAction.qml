// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1
import QtQuick.Dialogs 1.2 // For filedialog

import UM 1.2 as UM
import Cura 1.0 as Cura


Cura.MachineAction
{
    anchors.fill: parent;
    property bool printerConnected: Cura.MachineManager.printerConnected
    property var activeOutputDevice: printerConnected ? Cura.MachineManager.printerOutputDevices[0] : null
    property bool canUpdateFirmware: activeOutputDevice ? activeOutputDevice.activePrinter.canUpdateFirmware : false

    Column
    {
        id: firmwareUpdaterMachineAction
        anchors.fill: parent;
        UM.I18nCatalog { id: catalog; name: "cura"}
        spacing: UM.Theme.getSize("default_margin").height

        Label
        {
            width: parent.width
            text: catalog.i18nc("@title", "Update Firmware")
            wrapMode: Text.WordWrap
            font.pointSize: 18
        }
        Label
        {
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "Firmware is the piece of software running directly on your 3D printer. This firmware controls the step motors, regulates the temperature and ultimately makes your printer work.")
        }

        Label
        {
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "The firmware shipping with new printers works, but new versions tend to have more features and improvements.");
        }

        Row
        {
            anchors.horizontalCenter: parent.horizontalCenter
            width: childrenRect.width
            spacing: UM.Theme.getSize("default_margin").width
            property string firmwareName: Cura.MachineManager.activeMachine.getDefaultFirmwareName()
            Button
            {
                id: autoUpgradeButton
                text: catalog.i18nc("@action:button", "Automatically upgrade Firmware");
                enabled: parent.firmwareName != "" && canUpdateFirmware
                onClicked:
                {
                    updateProgressDialog.visible = true;
                    activeOutputDevice.updateFirmware(parent.firmwareName);
                }
            }
            Button
            {
                id: manualUpgradeButton
                text: catalog.i18nc("@action:button", "Upload custom Firmware");
                enabled: canUpdateFirmware
                onClicked:
                {
                    customFirmwareDialog.open()
                }
            }
        }

        Label
        {
            width: parent.width
            wrapMode: Text.WordWrap
            visible: !printerConnected && !updateProgressDialog.visible
            text: catalog.i18nc("@label", "Firmware can not be updated because there is no connection with the printer.");
        }

        Label
        {
            width: parent.width
            wrapMode: Text.WordWrap
            visible: printerConnected && !canUpdateFirmware
            text: catalog.i18nc("@label", "Firmware can not be updated because the connection with the printer does not support upgrading firmware.");
        }
    }

    FileDialog
    {
        id: customFirmwareDialog
        title: catalog.i18nc("@title:window", "Select custom firmware")
        nameFilters:  "Firmware image files (*.hex)"
        selectExisting: true
        onAccepted:
        {
            updateProgressDialog.visible = true;
            activeOutputDevice.updateFirmware(fileUrl);
        }
    }

    UM.Dialog
    {
        id: updateProgressDialog

        width: minimumWidth
        minimumWidth: 500 * screenScaleFactor
        height: minimumHeight
        minimumHeight: 100 * screenScaleFactor

        modality: Qt.ApplicationModal

        title: catalog.i18nc("@title:window","Firmware Update")

        Column
        {
            anchors.fill: parent

            Label
            {
                anchors
                {
                    left: parent.left
                    right: parent.right
                }

                text: {
                    if(manager.firmwareUpdater == null)
                    {
                        return "";
                    }
                    switch (manager.firmwareUpdater.firmwareUpdateState)
                    {
                        case 0:
                            return ""; //Not doing anything (eg; idling)
                        case 1:
                            return catalog.i18nc("@label","Updating firmware.");
                        case 2:
                            return catalog.i18nc("@label","Firmware update completed.");
                        case 3:
                            return catalog.i18nc("@label","Firmware update failed due to an unknown error.");
                        case 4:
                            return catalog.i18nc("@label","Firmware update failed due to an communication error.");
                        case 5:
                            return catalog.i18nc("@label","Firmware update failed due to an input/output error.");
                        case 6:
                            return catalog.i18nc("@label","Firmware update failed due to missing firmware.");
                    }
                }

                wrapMode: Text.Wrap
            }

            ProgressBar
            {
                id: prog
                value: (manager.firmwareUpdater != null) ? manager.firmwareUpdater.firmwareProgress : 0
                minimumValue: 0
                maximumValue: 100
                indeterminate:
                {
                    if(manager.firmwareUpdater == null)
                    {
                        return false;
                    }
                    return manager.firmwareUpdater.firmwareProgress < 1 && manager.firmwareUpdater.firmwareProgress > 0;
                }
                anchors
                {
                    left: parent.left;
                    right: parent.right;
                }
            }
        }

        rightButtons: [
            Button
            {
                text: catalog.i18nc("@action:button","Close");
                enabled: (manager.firmwareUpdater != null) ? manager.firmwareUpdater.firmwareUpdateState != 1 : true;
                onClicked: updateProgressDialog.visible = false;
            }
        ]
    }
}