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

    // If there's a manual address resolve request in progress.
    property bool hasRequestInProgress: CuraApplication.getDiscoveredPrintersModel().hasManualDeviceRequestInProgress
    // Indicates if a request has finished.
    property bool hasRequestFinished: false

    property var discoveredPrinter: null
    property var isPrinterDiscovered: discoveredPrinter != null

    // Make sure to cancel the current request when this page closes.
    onVisibleChanged:
    {
        if (!visible)
        {
            CuraApplication.getDiscoveredPrintersModel().cancelCurrentManualDeviceRequest()
        }
    }

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Add printer by IP address")
        color: UM.Theme.getColor("primary_button")
        font: UM.Theme.getFont("huge")
        renderType: Text.NativeRendering
    }

    Item
    {
        anchors.top: titleLabel.bottom
        anchors.bottom: connectButton.top
        anchors.topMargin: UM.Theme.getSize("default_margin").height
        anchors.bottomMargin: UM.Theme.getSize("default_margin").height
        anchors.left: parent.left
        anchors.right: parent.right

        Item
        {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: UM.Theme.getSize("default_margin").width

            Label
            {
                id: explainLabel
                height: contentHeight
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top

                font: UM.Theme.getFont("default")
                color: UM.Theme.getColor("text")
                renderType: Text.NativeRendering
                text: catalog.i18nc("@label", "Enter the IP address or hostname of your printer on the network.")
            }

            Item
            {
                id: userInputFields
                height: childrenRect.height
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: explainLabel.bottom
                anchors.topMargin: UM.Theme.getSize("default_margin").width

                Cura.TextField
                {
                    id: hostnameField
                    width: (parent.width / 2) | 0
                    height: addPrinterButton.height
                    anchors.verticalCenter: addPrinterButton.verticalCenter
                    anchors.left: parent.left

                    validator: RegExpValidator
                    {
                        regExp: /((^\s*((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))\s*$)|(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$))?/
                    }

                    placeholderText: catalog.i18nc("@text", "Place enter your printer's IP address.")

                    enabled: { ! (addPrinterByIpScreen.hasRequestInProgress || addPrinterByIpScreen.isPrinterDiscovered) }
                    onAccepted: addPrinterButton.clicked()
                }

                Cura.SecondaryButton
                {
                    id: addPrinterButton
                    anchors.top: parent.top
                    anchors.left: hostnameField.right
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    text: catalog.i18nc("@button", "Add")
                    enabled: !addPrinterByIpScreen.hasRequestInProgress && !addPrinterByIpScreen.isPrinterDiscovered && (hostnameField.state != "invalid" && hostnameField.text != "")
                    onClicked:
                    {
                        const address = hostnameField.text

                        // This address is already in the discovered printer model, no need to add a manual discovery.
                        if (CuraApplication.getDiscoveredPrintersModel().discoveredPrintersByAddress[address])
                        {
                            addPrinterByIpScreen.discoveredPrinter = CuraApplication.getDiscoveredPrintersModel().discoveredPrintersByAddress[address]
                            return
                        }

                        CuraApplication.getDiscoveredPrintersModel().checkManualDevice(address)
                    }
                    busy: addPrinterByIpScreen.hasRequestInProgress
                }
            }

            Item
            {
                width: parent.width
                anchors.top: userInputFields.bottom
                anchors.margins: UM.Theme.getSize("default_margin").width

                Label
                {
                    id: waitResponseLabel
                    anchors.top: parent.top
                    anchors.margins: UM.Theme.getSize("default_margin").width
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering

                    visible: addPrinterByIpScreen.hasRequestInProgress || (addPrinterByIpScreen.hasRequestFinished && !addPrinterByIpScreen.isPrinterDiscovered)
                    text:
                    {
                        if (addPrinterByIpScreen.hasRequestFinished)
                        {
                            catalog.i18nc("@label", "Could not connect to device.")
                        }
                        else
                        {
                            catalog.i18nc("@label", "The printer at this address has not responded yet.")
                        }
                    }
                }

                Item
                {
                    id: printerInfoLabels
                    anchors.top: parent.top
                    anchors.margins: UM.Theme.getSize("default_margin").width

                    visible: addPrinterByIpScreen.isPrinterDiscovered

                    Label
                    {
                        id: printerNameLabel
                        anchors.top: parent.top
                        font: UM.Theme.getFont("large")
                        color: UM.Theme.getColor("text")
                        renderType: Text.NativeRendering

                        text: !addPrinterByIpScreen.isPrinterDiscovered ? "???" : addPrinterByIpScreen.discoveredPrinter.name
                    }

                    GridLayout
                    {
                        id: printerInfoGrid
                        anchors.top: printerNameLabel.bottom
                        anchors.margins: UM.Theme.getSize("default_margin").width
                        columns: 2
                        columnSpacing: UM.Theme.getSize("default_margin").width

                        Label
                        {
                            text: catalog.i18nc("@label", "Type")
                            font: UM.Theme.getFont("default")
                            color: UM.Theme.getColor("text")
                            renderType: Text.NativeRendering
                        }
                        Label
                        {
                            id: typeText
                            text: !addPrinterByIpScreen.isPrinterDiscovered ? "?" : addPrinterByIpScreen.discoveredPrinter.readableMachineType
                            font: UM.Theme.getFont("default")
                            color: UM.Theme.getColor("text")
                            renderType: Text.NativeRendering
                        }

                        Label
                        {
                            text: catalog.i18nc("@label", "Firmware version")
                            font: UM.Theme.getFont("default")
                            color: UM.Theme.getColor("text")
                            renderType: Text.NativeRendering
                        }
                        Label
                        {
                            id: firmwareText
                            text: !addPrinterByIpScreen.isPrinterDiscovered ? "0.0.0.0" : addPrinterByIpScreen.discoveredPrinter.device.getProperty("firmware_version")
                            font: UM.Theme.getFont("default")
                            color: UM.Theme.getColor("text")
                            renderType: Text.NativeRendering
                        }

                        Label
                        {
                            text: catalog.i18nc("@label", "Address")
                            font: UM.Theme.getFont("default")
                            color: UM.Theme.getColor("text")
                            renderType: Text.NativeRendering
                        }
                        Label
                        {
                            id: addressText
                            text: !addPrinterByIpScreen.isPrinterDiscovered ? "0.0.0.0" : addPrinterByIpScreen.discoveredPrinter.address
                            font: UM.Theme.getFont("default")
                            color: UM.Theme.getColor("text")
                            renderType: Text.NativeRendering
                        }
                    }

                    Connections
                    {
                        target: CuraApplication.getDiscoveredPrintersModel()
                        onManualDeviceRequestFinished:
                        {
                            var discovered_printers_model = CuraApplication.getDiscoveredPrintersModel()
                            var printer = discovered_printers_model.discoveredPrintersByAddress[hostnameField.text]
                            if (printer)
                            {
                                addPrinterByIpScreen.discoveredPrinter = printer
                            }
                            addPrinterByIpScreen.hasRequestFinished = true
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
        text: catalog.i18nc("@button", "Back")
        onClicked:
        {
            CuraApplication.getDiscoveredPrintersModel().cancelCurrentManualDeviceRequest()
            base.showPreviousPage()
        }
    }

    Cura.PrimaryButton
    {
        id: connectButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: catalog.i18nc("@button", "Connect")
        onClicked:
        {
            CuraApplication.getDiscoveredPrintersModel().createMachineFromDiscoveredPrinter(discoveredPrinter)
            base.showNextPage()
        }

        enabled: addPrinterByIpScreen.isPrinterDiscovered
    }
}
