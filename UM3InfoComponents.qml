import UM 1.2 as UM
import Cura 1.0 as Cura

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

Item
{
    id: base

    property bool isUM3: Cura.MachineManager.activeDefinitionId == "ultimaker3"
    property bool printerConnected: Cura.MachineManager.printerOutputDevices.length != 0
    property bool printerAcceptsCommands: printerConnected && Cura.MachineManager.printerOutputDevices[0].acceptsCommands

    Row
    {
        objectName: "networkPrinterConnectButton"
        visible: isUM3
        spacing: UM.Theme.getSize("default_marging").width

        Button
        {
            height: UM.Theme.getSize("save_button_save_to_button").height
            tooltip: catalog.i18nc("@info:tooltip", "Send access request to the printer")
            text: catalog.i18nc("@action:button", "Request Access")
            style: UM.Theme.styles.sidebar_action_button
            onClicked: Cura.MachineManager.printerOutputDevices[0].requestAuthentication()
            visible: base.printerConnected && !base.printerAcceptsCommands
        }

        Button
        {
            height: UM.Theme.getSize("save_button_save_to_button").height
            tooltip: catalog.i18nc("@info:tooltip", "Connect to a printer")
            text: catalog.i18nc("@action:button", "Connect")
            style: UM.Theme.styles.sidebar_action_button
            onClicked: connectActionDialog.show()
            visible: !base.printerConnected
        }
    }

    UM.Dialog
    {
        id: connectActionDialog
        Loader
        {
            anchors.fill: parent
            source: "DiscoverUM3Action.qml"
        }
        rightButtons: Button
        {
            text: catalog.i18nc("@action:button", "Close")
            iconName: "dialog-close"
            onClicked: connectActionDialog.reject()
        }
    }


    Item
    {
        objectName: "networkPrinterConnectionInfo"
        visible: isUM3
        Button
        {
            tooltip: catalog.i18nc("@info:tooltip", "Send access request to the printer")
            text: catalog.i18nc("@action:button", "Request Access")
            onClicked: Cura.MachineManager.printerOutputDevices[0].requestAuthentication()
            visible: base.printerConnected && !base.printerAcceptsCommands
        }

        Button
        {
            tooltip: catalog.i18nc("@info:tooltip", "Load the configuration of the printer into Cura")
            text: catalog.i18nc("@action:button", "Activate Configuration")
            visible: false
        }
    }

    UM.I18nCatalog{id: catalog; name:"cura"}
}