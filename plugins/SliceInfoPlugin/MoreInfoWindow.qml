// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Window 2.2
import QtQuick.Controls 1.4
import QtQuick.Controls.Styles 1.4

import UM 1.3 as UM
import Cura 1.0 as Cura


UM.Dialog
{
    id: baseDialog
    title: catalog.i18nc("@title:window", "More information on anonymous data collection")
    visible: false

    minimumWidth: 500 * screenScaleFactor
    minimumHeight: 400 * screenScaleFactor
    width: minimumWidth
    height: minimumHeight

    property bool allowSendData: true  // for saving the user's choice

    onAccepted: manager.setSendSliceInfo(allowSendData)

    onVisibilityChanged:
    {
        if (visible)
        {
            baseDialog.allowSendData = UM.Preferences.getValue("info/send_slice_info");
            if (baseDialog.allowSendData)
            {
                allowSendButton.checked = true;
            }
            else
            {
                dontSendButton.checked = true;
            }
        }
    }

    Item
    {
        id: textRow
        anchors
        {
            top: parent.top
            bottom: radioButtonsRow.top
            bottomMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            right: parent.right
        }

        Label
        {
            id: headerText
            anchors
            {
                top: parent.top
                left: parent.left
                right: parent.right
            }

            text: catalog.i18nc("@text:window", "Cura sends anonymous data to Ultimaker in order to improve the print quality and user experience. Below is an example of all the data that is sent.")
            wrapMode: Text.WordWrap
        }

        TextArea
        {
            id: exampleData
            anchors
            {
                top: headerText.bottom
                topMargin: UM.Theme.getSize("default_margin").height
                bottom: parent.bottom
                bottomMargin: UM.Theme.getSize("default_margin").height
                left: parent.left
                right: parent.right
            }

            text: manager.getExampleData()
            readOnly: true
            textFormat: TextEdit.PlainText
        }
    }

    Column
    {
        id: radioButtonsRow
        width: parent.width
        anchors.bottom: buttonRow.top
        anchors.bottomMargin: UM.Theme.getSize("default_margin").height

        ExclusiveGroup { id: group }

        RadioButton
        {
            id: dontSendButton
            text: catalog.i18nc("@text:window", "I don't want to send this data")
            exclusiveGroup: group
            onClicked:
            {
                baseDialog.allowSendData = !checked;
            }
        }
        RadioButton
        {
            id: allowSendButton
            text: catalog.i18nc("@text:window", "Allow sending this data to Ultimaker and help us improve Cura")
            exclusiveGroup: group
            onClicked:
            {
                baseDialog.allowSendData = checked;
            }
        }
    }

    Item
    {
        id: buttonRow
        anchors.bottom: parent.bottom
        width: parent.width
        anchors.bottomMargin: UM.Theme.getSize("default_margin").height

        UM.I18nCatalog { id: catalog; name: "cura" }

        Button
        {
            anchors.right: parent.right
            text: catalog.i18nc("@action:button", "OK")
            onClicked:
            {
                baseDialog.accepted()
                baseDialog.hide()
            }
        }

        Button
        {
            anchors.left: parent.left
            text: catalog.i18nc("@action:button", "Cancel")
            onClicked:
            {
                baseDialog.rejected()
                baseDialog.hide()
            }
        }
    }
}
