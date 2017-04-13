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

        Row
        {
            spacing: UM.Theme.getSize("default_margin").width
            Label
            {
                text: catalog.i18nc("@label", "Port:")
                anchors.verticalCenter: parent.verticalCenter
            }
            ComboBox
            {
                model: ["COM3", "COM4", "COM5"]
                anchors.verticalCenter: parent.verticalCenter
            }
            Label
            {
                text: catalog.i18nc("@label", "Communication Speed:")
                anchors.verticalCenter: parent.verticalCenter
            }
            ComboBox
            {
                model: [250000, 230400, 115200, 57600, 38400, 19200, 9600]
                anchors.verticalCenter: parent.verticalCenter
            }
            Button
            {
                text: catalog.i18nc("@action:button", "Detect")
            }
        }

        CheckBox
        {
            text: catalog.i18nc("@label", "Automatically detect this printer on startup if the connection seems to have changed.")
            checked: true
        }

        Label
        {
            width: parent.width
            wrapMode: Text.WordWrap
            text: catalog.i18nc("@label", "Note: detecting printers may reset devices connected to this computer, and may interrupt an ongoing print on a USB-connected printer.")
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