// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the 'by IP' page of the "Add New Printer" flow of the on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    id: addPrinterByIpScreen

    property bool hasPushedAdd: false
    property bool hasSentRequest: false
    property bool haveConnection: false

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.topMargin: 40
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Add printer by IP address")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("large_bold")
        renderType: Text.NativeRendering
    }

    Rectangle
    {
        anchors.top: titleLabel.bottom
        anchors.bottom: connectButton.top
        anchors.topMargin: 40
        anchors.bottomMargin: 40
        anchors.horizontalCenter: parent.horizontalCenter
        width: parent.width * 3 / 4

        Item
        {
            width: parent.width

            Label
            {
                id: explainLabel
                height: contentHeight
                width: parent.width
                anchors.top: parent.top
                anchors.margins: 20
                font: UM.Theme.getFont("default")

                text: catalog.i18nc("@label", "Enter the IP address or hostname of your printer on the network.")
            }

            Item
            {
                id: userInputFields
                height: childrenRect.height
                width: parent.width
                anchors.top: explainLabel.bottom

                TextField
                {
                    id: hostnameField
                    anchors.verticalCenter: addPrinterButton.verticalCenter
                    anchors.left: parent.left
                    height: addPrinterButton.height
                    anchors.right: addPrinterButton.left
                    anchors.margins: 20
                    font: UM.Theme.getFont("default")

                    text: ""

                    validator: RegExpValidator
                    {
                        regExp: /[a-zA-Z0-9\.\-\_]*/
                    }

                    onAccepted: addPrinterButton.clicked()
                }

                Cura.PrimaryButton
                {
                    id: addPrinterButton
                    anchors.top: parent.top
                    anchors.right: parent.right
                    anchors.margins: 20
                    width: 140
                    fixedWidthMode: true

                    text: catalog.i18nc("@button", "Add")
                    onClicked:
                    {
                        if (hostnameField.text.trim() != "")
                        {
                            addPrinterByIpScreen.hasPushedAdd = true
                            UM.OutputDeviceManager.addManualDevice(hostnameField.text, hostnameField.text)
                        }
                    }

                    enabled: ! addPrinterByIpScreen.hasPushedAdd
                    BusyIndicator
                    {
                        anchors.fill: parent
                        running:
                        {
                            ! parent.enabled &&
                            ! addPrinterByIpScreen.hasSentRequest &&
                            ! addPrinterByIpScreen.haveConnection
                        }
                    }
                }
            }

            Rectangle
            {
                width: parent.width
                anchors.top: userInputFields.bottom
                anchors.margins: 20

                Label
                {
                    id: waitResponseLabel
                    anchors.top: parent.top
                    anchors.margins: 20
                    font: UM.Theme.getFont("default")

                    visible: { addPrinterByIpScreen.hasSentRequest && ! addPrinterByIpScreen.haveConnection }
                    text: catalog.i18nc("@label", "The printer at this address has not responded yet.")
                }

                Rectangle
                {
                    id: printerInfoLabels
                    anchors.top: parent.top
                    anchors.margins: 20

                    visible: addPrinterByIpScreen.haveConnection

                    Label
                    {
                        id: printerNameLabel
                        anchors.top: parent.top
                        font: UM.Theme.getFont("large")

                        text: "???"
                    }

                    GridLayout
                    {
                        id: printerInfoGrid
                        anchors.top: printerNameLabel.bottom
                        anchors.margins: 20
                        columns: 2
                        columnSpacing: 20

                        Label { font: UM.Theme.getFont("default"); text: catalog.i18nc("@label", "Type") }
                        Label { id: typeText; font: UM.Theme.getFont("default"); text: "?" }

                        Label { font: UM.Theme.getFont("default"); text: catalog.i18nc("@label", "Firmware version") }
                        Label { id: firmwareText; font: UM.Theme.getFont("default"); text: "0.0.0.0" }

                        Label { font: UM.Theme.getFont("default"); text: catalog.i18nc("@label", "Address") }
                        Label { id: addressText; font: UM.Theme.getFont("default"); text: "0.0.0.0" }

                        Connections
                        {
                            target: UM.OutputDeviceManager
                            onManualDeviceChanged:
                            {
                                typeText.text = UM.OutputDeviceManager.manualDeviceProperty("printer_type")
                                firmwareText.text = UM.OutputDeviceManager.manualDeviceProperty("firmware_version")
                                addressText.text = UM.OutputDeviceManager.manualDeviceProperty("address")
                            }
                        }
                    }

                    Connections
                    {
                        target: UM.OutputDeviceManager
                        onManualDeviceChanged:
                        {
                            printerNameLabel.text = UM.OutputDeviceManager.manualDeviceProperty("name")
                            addPrinterByIpScreen.haveConnection = true
                        }
                    }
                }
            }
        }
    }

    Cura.PrimaryButton
    {
        id: backButton
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.margins: 40
        text: catalog.i18nc("@button", "Cancel")
        width: 140
        fixedWidthMode: true
        onClicked: base.gotoPage("add_printer_by_selection")

        enabled: true
    }

    Cura.PrimaryButton
    {
        id: connectButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.margins: 40
        text: catalog.i18nc("@button", "Connect")
        width: 140
        fixedWidthMode: true
        onClicked:
        {
            CuraApplication.getDiscoveredPrintersModel().createMachineFromDiscoveredPrinterAddress(
                UM.OutputDeviceManager.manualDeviceProperty("address"))
            UM.OutputDeviceManager.setActiveDevice(UM.OutputDeviceManager.manualDeviceProperty("device_id"))
            base.showNextPage()
        }

        enabled: addPrinterByIpScreen.haveConnection
    }
}
