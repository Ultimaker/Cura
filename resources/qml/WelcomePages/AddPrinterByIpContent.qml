// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This component contains the content for the 'by IP' page of the "Add New Printer" flow of the on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

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

        border.color: "#dfdfdf"
        border.width: 1

        Item
        {
            width: parent.width
            //anchors.top: parent.top
            //anchors.topMargin: 20
            //anchors.bottomMargin: 20

            Label
            {
                id: explainLabel
                height: contentHeight
                width: parent.width
                anchors.top: parent.top
                anchors.margins: 20
                //anchors.bottomMargin: 20

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
                    anchors.top: parent.top
                    anchors.left: parent.left
                    //anchors.bottom: parent.bottom
                    anchors.right: addPrinterButton.left
                    anchors.margins: 20
                    //width: parent.width / 2
                    //horizontalAlignment: Text.AlignLeft

                    //editable: true
                    text: ""

                    //validator: RegExpValidator
                    //{
                    //    regExp: /[a-zA-Z0-9\.\-\_]*/
                    //}

                    onAccepted: addPrinterButton.clicked()
                }

                Cura.PrimaryButton
                {
                    id: addPrinterButton
                    anchors.top: parent.top
                    anchors.right: parent.right
                    //anchors.bottom: parent.bottom
                    anchors.margins: 20
                    width: 140
                    fixedWidthMode: true

                    text: catalog.i18nc("@button", "Add")
                    onClicked:
                    {
                        // fire off method, then wait for event


                        // manager.setManualDevice(manualPrinterDialog.printerKey, manualPrinterDialog.addressText)   // manager not defined
                        // manualPrinterDialog.hide()
                    }
                    //enabled: hostnameField.trim() != ""
                }
            }

            Rectangle
            {
                width: parent.width
                anchors.top: userInputFields.bottom

                Label
                {
                    id: visTestA
                    anchors.top: parent.top
                    anchors.margins: 20

                    visible: false
                    text: catalog.i18nc("@label", "The printer at this address has not responded yet.")
                }

                Label
                {
                    id: visTestB
                    anchors.top: parent.top
                    anchors.margins: 20

                    visible: true
                    text: "PLACEHOLDER"
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
        onClicked: base.showPreviousPage()  // TODO?

        enabled: true  // TODO
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

        enabled: false  // TODO
    }
}
