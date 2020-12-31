// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1
import UM 1.2 as UM
import Cura 1.0 as Cura

Item {
    id: base;
    property string activeQualityDefinitionId: Cura.MachineManager.activeQualityDefinitionId;
    property bool isUM3: activeQualityDefinitionId == "ultimaker3" || activeQualityDefinitionId.match("ultimaker_") != null;
    property bool printerConnected: Cura.MachineManager.printerConnected;
    property bool printerAcceptsCommands:
    {
        if (printerConnected && Cura.MachineManager.printerOutputDevices[0])
        {
            return Cura.MachineManager.printerOutputDevices[0].acceptsCommands
        }
        return false
    }
    property bool authenticationRequested:
    {
        if (printerConnected && Cura.MachineManager.printerOutputDevices[0])
        {
            var device = Cura.MachineManager.printerOutputDevices[0]
            // AuthState.AuthenticationRequested or AuthState.AuthenticationReceived
            return device.authenticationState == 2 || device.authenticationState == 5
        }
        return false
    }
    property var materialNames:
    {
        if (printerConnected && Cura.MachineManager.printerOutputDevices[0])
        {
            return Cura.MachineManager.printerOutputDevices[0].materialNames
        }
        return null
    }
    property var hotendIds:
    {
        if (printerConnected && Cura.MachineManager.printerOutputDevices[0])
        {
            return Cura.MachineManager.printerOutputDevices[0].hotendIds
        }
        return null
    }

    UM.I18nCatalog {
        id: catalog;
        name: "cura";
    }

    Row {
        objectName: "networkPrinterConnectButton";
        spacing: UM.Theme.getSize("default_margin").width;

        Button {
            height: UM.Theme.getSize("save_button_save_to_button").height;
            onClicked: Cura.MachineManager.printerOutputDevices[0].requestAuthentication();
            style: UM.Theme.styles.print_setup_action_button;
            text: catalog.i18nc("@action:button", "Request Access");
            tooltip: catalog.i18nc("@info:tooltip", "Send access request to the printer");
            visible: printerConnected && !printerAcceptsCommands && !authenticationRequested;
        }

        Button {
            height: UM.Theme.getSize("save_button_save_to_button").height;
            onClicked: connectActionDialog.show();
            style: UM.Theme.styles.print_setup_action_button;
            text: catalog.i18nc("@action:button", "Connect");
            tooltip: catalog.i18nc("@info:tooltip", "Connect to a printer");
            visible: !printerConnected;
        }
    }

    UM.Dialog {
        id: connectActionDialog;
        rightButtons: Button {
            iconName: "dialog-close";
            onClicked: connectActionDialog.reject();
            text: catalog.i18nc("@action:button", "Close");
        }

        Loader {
            anchors.fill: parent;
            source: "MachineConfig.qml";
        }
    }
}
