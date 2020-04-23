// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.5 as Cura


//
// This component contains the content for the 'by IP' page of the "Add New Printer" flow of the on-boarding process.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    id: addCloudPrinterScreen

    property bool searchingForCloudPrinters: true



    Rectangle
    {
        id: cloudPrintersContent
        //color: "steelblue"
        //opacity: 0.3
        width: parent.width
        border.width: 1
        anchors
        {
            top: parent.top
            bottom: finishButton.top
            left: parent.left
            right: parent.right
            bottomMargin: UM.Theme.getSize("default_margin").height
        }

        Label
        {
            id: titleLabel
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            text: catalog.i18nc("@label", "Add a Cloud printer")
            color: UM.Theme.getColor("primary_button")
            font: UM.Theme.getFont("huge")
            renderType: Text.NativeRendering
        }

        Rectangle
        {
            id: waitingContent
            width: parent.width
            height: waitingIndicator.height + waitingLabel.height
            border.width: 1
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            BusyIndicator
            {
                id: waitingIndicator
                anchors.horizontalCenter: parent.horizontalCenter
                running: searchingForCloudPrinters
            }
            Label
            {
                id: waitingLabel
                anchors.top: waitingIndicator.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: catalog.i18nc("@label", "Waiting for Cloud response")
                font: UM.Theme.getFont("medium")
                renderType: Text.NativeRendering
            }
            visible: false
        }


    }

    Cura.SecondaryButton
    {
        id: backButton
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        text: catalog.i18nc("@button", "Add printer manually")
        onClicked:
        {
            Cura.API.account.test("Back button pressed in AddCloudPrintersView.qml")
            base.showPreviousPage()
        }
    }

    Cura.PrimaryButton
    {
        id: finishButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: catalog.i18nc("@button", "Finish")
        onClicked:
        {
            Cura.API.account.test("Finish button pressed in AddCloudPrintersView.qml")
            base.showNextPage()
        }

        // enabled: 1 === 1 addPrinterByIpScreen.canAddPrinter
    }
}
