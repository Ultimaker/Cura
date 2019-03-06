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

    Timer
    {
        id: tempTimerButton

        interval: 1200
        running: false
        repeat: false
        onTriggered:
        {
            hasPushedAdd = true
            tempTimerRequest.running = true
        }
    }
    // TODO: Remove timers after review interface!

    Timer
    {
        id: tempTimerRequest

        interval: 1200
        running: false
        repeat: false
        onTriggered:
        {
            hasSentRequest = true
            tempTimerConnection.running = true
        }
    }
    // TODO: Remove timers after review interface!

    Timer
    {
        id: tempTimerConnection

        interval: 1200
        running: false
        repeat: false
        onTriggered: haveConnection = true
    }
    // TODO: Remove timers after review interface!

    Label
    {
        id: titleLabel
        anchors.top: parent.top
        anchors.topMargin: 40
        anchors.horizontalCenter: parent.horizontalCenter
        horizontalAlignment: Text.AlignHCenter
        text: catalog.i18nc("@label", "Add printer by IP adress")
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
                //anchors.bottomMargin: 20
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
                        // TEMP: Simulate successfull connection to printer with 127.0.0.1 or unsuccessful with anything else
                        // TODO, alter after review interface, now it just starts the timers.

                        if (hostnameField.text.trim() != "")
                        {
                            addPrinterByIpScreen.hasPushedAdd = true
                            tempTimerRequest.running = true

                            UM.OutputDeviceManager.addManualDevice(hostnameField.text, hostnameField.text)
                        }
                    }

                    enabled: ! addPrinterByIpScreen.hasPushedAdd
                    BusyIndicator
                    {
                        anchors.fill: parent
                        running: { ! parent.enabled && ! addPrinterByIpScreen.hasSentRequest }
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

                        text: "Davids-desktop"  // TODO: placeholder, alter after interface review.
                    }

                    GridLayout
                    {
                        anchors.top: printerNameLabel.bottom
                        columns: 2
                        columnSpacing: 20

                        Text { font: UM.Theme.getFont("default"); text: "Type" }
                        Text { font: UM.Theme.getFont("default"); text: "Ultimaker S5" }  // TODO: placeholder, alter after interface review.

                        Text { font: UM.Theme.getFont("default"); text: "Firmware version" }
                        Text { font: UM.Theme.getFont("default"); text: "4.3.3.20180529" }  // TODO: placeholder, alter after interface review.

                        Text { font: UM.Theme.getFont("default"); text: "Address" }
                        Text { font: UM.Theme.getFont("default"); text: "10.183.1.115" }  // TODO: placeholder, alter after interface review.
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
        text: catalog.i18nc("@button", "Back")
        width: 140
        fixedWidthMode: true
        onClicked: base.showPreviousPage()

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
        onClicked: base.showNextPage()

        enabled: addPrinterByIpScreen.haveConnection
    }
}
