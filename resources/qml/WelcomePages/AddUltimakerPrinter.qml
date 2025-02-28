// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3

import UM 1.5 as UM
import Cura 1.1 as Cura

Control
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    property var goToThirdPartyPrinter

    signal cloudPrintersDetected(bool newCloudPrintersDetected)
    Component.onCompleted: CuraApplication.getDiscoveredCloudPrintersModel().cloudPrintersDetectedChanged.connect(cloudPrintersDetected)
    onCloudPrintersDetected: function(newCloudPrintersDetected)
    {
        if(newCloudPrintersDetected)
        {
            base.goToPage("add_cloud_printers")
        }
    }

    contentItem: ColumnLayout
    {
        Layout.fillWidth: true
        UM.Label
        {
            Layout.fillWidth: true
            text: catalog.i18nc("@label", "New UltiMaker printers can be connected to Digital Factory and monitored remotely.")
            wrapMode: Text.WordWrap
        }

        RowLayout
        {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true

            Item
            {
                Layout.fillWidth: true
                Layout.minimumWidth: childrenRect.width
                Layout.preferredHeight: childrenRect.height

                Image
                {
                    anchors.right: parent.right
                    source: UM.Theme.getImage("add_printer")
                    Layout.preferredWidth: 200 * screenScaleFactor
                    Layout.preferredHeight: 200 * screenScaleFactor
                }
            }

            ColumnLayout
            {
                Layout.fillHeight: true
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignVCenter
                spacing: UM.Theme.getSize("default_margin").height

                UM.Label
                {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop
                    wrapMode: Text.WordWrap
                    font: UM.Theme.getFont("default_bold")
                    text: catalog.i18nc("@label", "If you are trying to add a new UltiMaker printer to Cura")
                }

                ColumnLayout
                {
                    spacing: 0
                    Layout.fillWidth: true

                    Repeater {
                        model: [
                            catalog.i18nc("@info", "Sign in into UltiMaker Digital Factory"),
                            catalog.i18nc("@info", "Follow the procedure to add a new printer"),
                            catalog.i18nc("@info", "Your new printer will automatically appear in Cura"),
                        ]
                        UM.Label
                        {
                            Layout.alignment: Qt.AlignTop
                            Layout.fillWidth: true
                            wrapMode: Text.WordWrap
                            text: `${index + 1}. ${modelData}`
                        }
                    }
                }

                Cura.TertiaryButton
                {
                    id: learnMoreButton
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignTop
                    leftPadding: 0
                    text: catalog.i18nc("@button", "Learn more")
                    iconSource: UM.Theme.getIcon("LinkExternal")
                    isIconOnRightSide: true
                    textFont: UM.Theme.getFont("small")
                    onClicked: Qt.openUrlExternally("https://support.ultimaker.com/hc/en-us/articles/360012019239?utm_source=cura&utm_medium=software&utm_campaign=onboarding-add-printer")
                }
            }
        }

        Control
        {
            Layout.alignment: Qt.AlignBottom
            Layout.fillWidth: true

            contentItem: RowLayout
            {

                Cura.SecondaryButton
                {
                    id: addLocalPrinterButton
                    Layout.alignment: Qt.AlignLeft
                    text: catalog.i18nc("@button", "Add local printer")
                    onClicked: goToThirdPartyPrinter()
                }

                Cura.PrimaryButton
                {
                    id: signInButton
                    Layout.alignment: Qt.AlignRight
                    text: catalog.i18nc("@button", "Sign in to Digital Factory")
                    onClicked: function()
                    {
                        Qt.openUrlExternally("https://digitalfactory.ultimaker.com/app/printers?add_printer=true&utm_source=cura&utm_medium=software&utm_campaign=onboarding-add-printer")
                        text = catalog.i18nc("@button", "Waiting for new printers")
                        busy = true;
                        enabled = false;
                        Cura.API.account.isLoggedIn? Cura.API.account.sync():Cura.API.account.login();
                    }
                }
            }
        }
    }
}
