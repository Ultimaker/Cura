// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Window 2.2
import QtQuick.Layouts

import UM 1.5 as UM
import Cura 1.1 as Cura

UM.Dialog
{
    id: baseDialog
    property variant catalog: UM.I18nCatalog { name: "cura" }
    title: catalog.i18nc("@title:window", "More information on anonymous data collection")
    visible: false

    minimumWidth: 500 * screenScaleFactor
    minimumHeight: 400 * screenScaleFactor
    width: minimumWidth
    height: minimumHeight

    color: UM.Theme.getColor("main_background")

    property bool allowSendData: true  // for saving the user's choice

    onAccepted: manager.setSendSliceInfo(allowSendData)

    onVisibilityChanged:
    {
        if (visible)
        {
            baseDialog.allowSendData = UM.Preferences.getValue("info/send_slice_info")
            if (baseDialog.allowSendData)
            {
                allowSendButton.checked = true
            }
            else
            {
                dontSendButton.checked = true
            }
        }
    }

    // Main content area
    ColumnLayout
    {
        anchors.fill: parent
        spacing: UM.Theme.getSize("default_margin").width

        UM.Label
        {
            id: headerText
            Layout.fillWidth: true
            text: catalog.i18nc("@text:window", "UltiMaker Cura collects anonymous data in order to improve the print quality and user experience. Below is an example of all the data that is shared:")
            wrapMode: Text.WordWrap
        }

        Cura.ScrollableTextArea
        {
            Layout.fillWidth: true
            Layout.fillHeight: true

            textArea.text: (manager === null) ? "" : manager.getExampleData()
            textArea.textFormat: Text.RichText
            textArea.wrapMode: Text.Wrap
            textArea.readOnly: true
        }

        ColumnLayout
        {
            spacing: 0

            Cura.RadioButton
            {
                id: dontSendButton
                text: catalog.i18nc("@text:window", "I don't want to send anonymous data")
                onClicked: baseDialog.allowSendData = !checked
            }

            Cura.RadioButton
            {
                id: allowSendButton
                text: catalog.i18nc("@text:window", "Allow sending anonymous data")
                onClicked: baseDialog.allowSendData = checked
            }
        }
    }

    rightButtons:
    [
        Cura.PrimaryButton
        {
            text: catalog.i18nc("@action:button", "OK")
            onClicked: baseDialog.accept()
        }
    ]

    leftButtons:
    [
        Cura.SecondaryButton
        {
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked: baseDialog.reject()
        }
    ]
}
