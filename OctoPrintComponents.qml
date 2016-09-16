import UM 1.2 as UM
import Cura 1.0 as Cura

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

Item
{
    id: base

    property string octoPrintConnected: printerConnected && Cura.MachineManager.printerOutputDevices[0].hasOwnProperty("octoprintVersion")
    property bool printerConnected: Cura.MachineManager.printerOutputDevices.length != 0
    property bool printerAcceptsCommands: printerConnected && Cura.MachineManager.printerOutputDevices[0].acceptsCommands
    property bool authenticationRequested: printerConnected && Cura.MachineManager.printerOutputDevices[0].authenticationState == 2 // AuthState.AuthenticationRequested

    Button
    {
        objectName: "openOctoPrintButton"
        height: UM.Theme.getSize("save_button_save_to_button").height
        tooltip: catalog.i18nc("@info:tooltip", "Open the OctoPrint web interface")
        text: catalog.i18nc("@action:button", "Open OctoPrint")
        style: UM.Theme.styles.sidebar_action_button
        onClicked: manager.openWebPage("http://%1/".arg(Cura.MachineManager.printerOutputDevices[0].ipAddress))
        visible: octoPrintConnected
    }

    UM.I18nCatalog{id: catalog; name:"cura"}
}