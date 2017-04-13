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
                model:
                {
                    var port_list = Cura.USBPrinterManager.portList
                    port_list.unshift("NONE", "AUTO")
                    return port_list
                }
            }
            Label
            {
                text:
                {
                    if (connectionPort.currentText == "AUTO")
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
                model: ["AUTO", "250000", "230400", "115200", "57600", "38400", "19200", "9600"]
                visible: connectionPort.currentText != "NONE"
            }
            Label
            {
                text:
                {
                    if (connectionRate.currentText == "AUTO")
                    {
                        return catalog.i18nc("@label", "Note: this selection will slow down detection of the connected printers.")
                    }
                    return "";
                }
                visible: connectionRate.visible
                Layout.fillWidth: true
                wrapMode: Text.WordWrap
            }

            Label
            {
                text: ""
            }
            Button
            {
                text: catalog.i18nc("@action:button", "Detect")
                visible: connectionPort.currentText != "NONE" && (connectionPort.currentText == "AUTO" || connectionRate.currentText == "AUTO")
            }
        }

        CheckBox
        {
            id: autoConnect
            text: catalog.i18nc("@label", "Automatically connect this printer on startup.")
            checked: true
            enabled: false
        }

        Label
        {
            width: parent.width
            wrapMode: Text.WordWrap
            visible: autoConnect.checked
            text: catalog.i18nc("@label", "Note: connecting to a printer will interrupt ongoing prints on the printer.")
        }

        Button
        {
            text: catalog.i18nc("@action:button", "Test Communication")
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