// Copyright (c) 2022 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.7 as Cura


//
// This component gets activated when the user presses the "Add cloud printers" button from the "Add a Printer" page.
// It contains a busy indicator that remains active until the user logs in and adds a cloud printer in his/her account.
// Once a cloud printer is added in digitalfactory.ultimaker.com, Cura discovers it (in a time window of 30 sec) and displays
// the newly added printers in this page.
//
Item
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    property bool searchingForCloudPrinters: true
    property var discoveredCloudPrintersModel: CuraApplication.getDiscoveredCloudPrintersModel()

    // The area where either the discoveredCloudPrintersList or the busyIndicator will be displayed
    Item
    {
        id: cloudPrintersContent
        width: parent.width
        height: parent.height
        anchors
        {
            top: parent.top
            left: parent.left
            leftMargin: UM.Theme.getSize("default_margin").width
            right: parent.right
            bottom: finishButton.top
            bottomMargin: UM.Theme.getSize("default_margin").height
        }

        UM.Label
        {
            id: titleLabel
            anchors.top: parent.top
            anchors.horizontalCenter: parent.horizontalCenter
            horizontalAlignment: Text.AlignHCenter
            text: catalog.i18nc("@label", "Add a Cloud printer")
            color: UM.Theme.getColor("primary_button")
            font: UM.Theme.getFont("huge")
        }

        // Component that contains a busy indicator and a message, while it waits for Cura to discover a cloud printer
        Item
        {
            id: waitingContent
            width: parent.width
            height: childrenRect.height
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            BusyIndicator
            {
                id: waitingIndicator
                anchors.horizontalCenter: parent.horizontalCenter
                running: searchingForCloudPrinters
                palette.dark: UM.Theme.getColor("text")
            }
            UM.Label
            {
                id: waitingLabel
                anchors.top: waitingIndicator.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: catalog.i18nc("@label", "Waiting for Cloud response")
                font: UM.Theme.getFont("large")
            }
            UM.Label
            {
                id: noPrintersFoundLabel
                anchors.top: waitingLabel.bottom
                anchors.topMargin: 2 * UM.Theme.getSize("wide_margin").height
                anchors.horizontalCenter: parent.horizontalCenter
                horizontalAlignment: Text.AlignHCenter
                text: catalog.i18nc("@label", "No printers found in your account?")
                font: UM.Theme.getFont("medium")
            }
            UM.Label
            {
                text: "Sign in with a different account"
                anchors.top: noPrintersFoundLabel.bottom
                anchors.horizontalCenter: parent.horizontalCenter
                font: UM.Theme.getFont("medium")
                color: UM.Theme.getColor("text_link")
                MouseArea {
                    anchors.fill: parent;
                    onClicked: Cura.API.account.login(true)
                    hoverEnabled: true
                    onEntered:
                    {
                        parent.font.underline = true
                    }
                    onExited:
                    {
                        parent.font.underline = false
                    }
                }
            }
            visible: discoveredCloudPrintersModel.count == 0
        }

        // Label displayed when a new cloud printer is discovered
        UM.Label
        {
            anchors.top: titleLabel.bottom
            anchors.topMargin: 2 * UM.Theme.getSize("default_margin").height
            id: cloudPrintersAddedTitle
            font: UM.Theme.getFont("medium")
            text: catalog.i18nc("@label", "The following printers in your account have been added in Cura:")
            height: contentHeight + 2 * UM.Theme.getSize("default_margin").height
            visible: discoveredCloudPrintersModel.count > 0
        }

        // The scrollView that contains the list of newly discovered Ultimaker Cloud printers. Visible only when
        // there is at least a new cloud printer.
        ListView
        {
            id: discoveredCloudPrintersList
            anchors
            {
                top: cloudPrintersAddedTitle.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                left: parent.left
                leftMargin: UM.Theme.getSize("default_margin").width
                right: parent.right
                bottom: parent.bottom
            }

            ScrollBar.vertical: UM.ScrollBar {}
            clip : true
            visible: discoveredCloudPrintersModel.count > 0
            spacing: UM.Theme.getSize("wide_margin").height

            model: discoveredCloudPrintersModel
            delegate: Item
            {
                width: discoveredCloudPrintersList.width
                height: contentColumn.height

                Column
                {
                    id: contentColumn
                    UM.Label
                    {
                        id: cloudPrinterNameLabel
                        leftPadding: UM.Theme.getSize("default_margin").width
                        text: model.name ? model.name : ""
                        font: UM.Theme.getFont("large_bold")
                        elide: Text.ElideRight
                    }
                    UM.Label
                    {
                        id: cloudPrinterTypeLabel
                        leftPadding: 2 * UM.Theme.getSize("default_margin").width
                        topPadding: UM.Theme.getSize("thin_margin").height
                        text: "Type: " + model.machine_type
                        font: UM.Theme.getFont("medium")
                        elide: Text.ElideRight
                    }
                    UM.Label
                    {
                        id: cloudPrinterFirmwareVersionLabel
                        leftPadding: 2 * UM.Theme.getSize("default_margin").width
                        text: "Firmware version: " + model.firmware_version
                        font: UM.Theme.getFont("medium")
                        elide: Text.ElideRight
                    }
                }
            }
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
            discoveredCloudPrintersModel.clear()
            base.showPreviousPage()
        }
        visible: discoveredCloudPrintersModel.count == 0
    }

    Cura.PrimaryButton
    {
        id: finishButton
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        text: base.currentItem.next_page_button_text
        onClicked:
        {
            discoveredCloudPrintersModel.clear()
            base.showNextPage()
        }

        enabled: !waitingContent.visible
    }
}
