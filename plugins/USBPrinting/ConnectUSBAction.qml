import UM 1.2 as UM
import Cura 1.0 as Cura

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

Cura.MachineAction
{
    id: base
    anchors.fill: parent;
    property var selectedInstance: null
    Column
    {
        anchors.fill: parent;
        id: discoverOctoPrintAction

        spacing: UM.Theme.getSize("default_margin").height

        SystemPalette { id: palette }
        UM.I18nCatalog { id: catalog; name:"cura" }
        Label
        {
            id: pageTitle
            width: parent.width
            text: catalog.i18nc("@title", "Connect via USB")
            wrapMode: Text.WordWrap
            font.pointSize: 18
        }

        Label
        {
            id: pageDescription
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "Select the port and communication speed to use to connect with this printer.")
        }

        GridLayout
        {
            width: parent.width
            columns: 3
            columnSpacing: UM.Theme.getSize("default_margin").width
            rowSpacing: UM.Theme.getSize("default_lining").height

            Label
            {
                text: catalog.i18nc("@label", "Serial Port:")
            }
            ComboBox
            {
                id: connectionPort

                property bool populatingModel: false
                model: ListModel
                {
                    id: connectionPortModel

                    Component.onCompleted: populateModel()

                    function populateModel()
                    {
                        connectionPort.populatingModel = true;
                        clear();

                        append({key: "NONE", text: catalog.i18nc("@label", "Don't connect")});
                        append({key: "AUTO", text: catalog.i18nc("@label", "Autodetect")});
                        var current_index = (manager.serialPort == "AUTO") ? 1:0;

                        var port_list = Cura.USBPrinterManager.portList;
                        for(var index in port_list)
                        {
                            append({key: port_list[index], text: port_list[index]});
                            if(port_list[index] == manager.serialPort)
                            {
                                current_index = parseInt(index) + 2;
                            }
                        }

                        if(current_index == 0 && manager.serialPort != "NONE")
                        {
                            append({key: manager.serialPort, text: catalog.i18nc("@label", "%1 (not available)").arg(manager.serialPort)});
                            current_index = count - 1;
                        }

                        connectionPort.currentIndex = current_index;
                        connectionPort.populatingModel = false;
                    }
                }
                onActivated:
                {
                    if(!populatingModel && model.get(index))
                    {
                        manager.setSerialPort(model.get(index).key);
                    }
                }

                Connections
                {
                    target: Cura.USBPrinterManager
                    onSerialPortsChanged: connectionPortModel.populateModel()
                }

            }
            Label
            {
                text:
                {
                    if (connectionPortModel.get(connectionPort.currentIndex).key == "AUTO")
                    {
                        return catalog.i18nc("@label", "Note: this selection will result in Cura scanning all serial ports which may reset connected devices.");
                    }
                    return "";
                }
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }
            Label
            {
                text: catalog.i18nc("@label", "Connection Speed:")
                visible: connectionRate.visible
            }
            ComboBox
            {
                id: connectionRate
                model: [
                    {key: "AUTO", text: catalog.i18nc("@label", "Autodetect")},
                    {key: "250000", text: "250000"},
                    {key: "230400", text: "230400"},
                    {key: "115200", text: "115200"},
                    {key: "57600", text: "57600"},
                    {key: "38400", text: "38400"},
                    {key: "19200", text: "19200"},
                    {key: "9600", text: "9600"},
                ]
                visible: connectionPortModel.get(connectionPort.currentIndex).key != "NONE"
                currentIndex:
                {
                    for(var index in model)
                    {
                        if(model[index].key == manager.serialRate)
                        {
                            return index;
                        }
                    }
                    return 0; // default to "AUTO"
                }
                onActivated: manager.setSerialRate(model[index].key)
            }
            Label
            {
                text:
                {
                    if (connectionRate.model[connectionRate.currentIndex].key == "AUTO")
                    {
                        return catalog.i18nc("@label", "Note: this selection will slow down detection of the connected printers.")
                    }
                    return "";
                }
                visible: connectionRate.visible
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }

            Label { text: ""; visible: detectButton.visible }
            Button
            {
                id: detectButton
                text: catalog.i18nc("@action:button", "Detect")
                visible: connectionPortModel.get(connectionPort.currentIndex).key != "NONE" && (connectionPortModel.get(connectionPort.currentIndex).key == "AUTO" || connectionRate.model[connectionRate.currentIndex].key == "AUTO")
            }
            Label { text: ""; visible: detectButton.visible }
        }

        CheckBox
        {
            id: listAllSerialPortsCheckBox
            text: catalog.i18nc("@label", "Only list USB serial ports.")
            checked: !UM.Preferences.getValue("usb_printing/list_all_serial_ports")
            onClicked: Cura.USBPrinterManager.setListAllSerialPorts(!checked)
        }

        CheckBox
        {
            id: autoConnect
            text: catalog.i18nc("@label", "Automatically connect this printer on startup.")
            checked: manager.autoConnect
            visible: connectionPortModel.get(connectionPort.currentIndex).key != "NONE"
            onClicked: manager.setAutoConnect(checked)
        }

        Label
        {
            width: parent.width
            wrapMode: Text.WordWrap
            visible: autoConnect.visible && autoConnect.checked
            text: catalog.i18nc("@label", "Note: connecting to a printer will interrupt ongoing prints on the printer.")
        }

        Button
        {
            id: testCommunication
            text: catalog.i18nc("@action:button", "Test Communication")
            visible: connectionPortModel.get(connectionPort.currentIndex).key != "NONE"
            onClicked: testOutput.visible = true
        }

        TextArea
        {
            id: testOutput
            visible: false
            text: "Sent: M105\nReceived: T:19.6 /0.0 B:16.8 /0.0 B@:0 @:0\n\nSent: M115\nReceived: FIRMWARE_NAME:Marlin Ultimaker2; Sprinter/grbl mashup for gen6 FIRMWARE_URL:http://github.com/Ultimaker PROTOCOL_VERSION:1.0 MACHINE_TYPE:Ultimaker EXTRUDER_COUNT:1"
            width: parent.width
            height: base.height - testOutput.y
        }
    }
}