// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3
import QtQuick.Window 2.2

import UM 1.3 as UM
import Cura 1.1 as Cura


Window
{
    UM.I18nCatalog { id: catalog; name: "cura" }

    id: baseDialog
    title: catalog.i18nc("@title:window", "More information on anonymous data collection")
    visible: false

    modality: Qt.ApplicationModal

    minimumWidth: 500 * screenScaleFactor
    minimumHeight: 400 * screenScaleFactor
    width: minimumWidth
    height: minimumHeight

    color: UM.Theme.getColor("main_background")

    property bool allowSendData: true  // for saving the user's choice

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
    Item
    {
        anchors.fill: parent
        anchors.margins: UM.Theme.getSize("default_margin").width

        Item  // Text part
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
                text: catalog.i18nc("@text:window", "Ultimaker Cura collects anonymous data in order to improve the print quality and user experience. Below is an example of all the data that is shared:")
                wrapMode: Text.WordWrap
                renderType: Text.NativeRendering
            }

            Cura.ScrollableTextArea
            {
                anchors
                {
                    top: headerText.bottom
                    topMargin: UM.Theme.getSize("default_margin").height
                    bottom: parent.bottom
                    bottomMargin: UM.Theme.getSize("default_margin").height
                    left: parent.left
                    right: parent.right
                }

                textArea.text: (manager === null) ? "" : manager.getExampleData()
                textArea.textFormat: Text.RichText
                textArea.wrapMode: Text.Wrap
                textArea.readOnly: true
            }
        }

        Column  // Radio buttons for agree and disagree
        {
            id: radioButtonsRow
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: buttonRow.top
            anchors.bottomMargin: UM.Theme.getSize("default_margin").height

            Cura.RadioButton
            {
                id: dontSendButton
                text: catalog.i18nc("@text:window", "I don't want to send anonymous data")
                onClicked:
                {
                    baseDialog.allowSendData = !checked
                }
            }
            Cura.RadioButton
            {
                id: allowSendButton
                text: catalog.i18nc("@text:window", "Allow sending anonymous data")
                onClicked:
                {
                    baseDialog.allowSendData = checked
                }
            }
        }

        Item  // Bottom buttons
        {
            id: buttonRow
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right

            height: childrenRect.height

            Cura.PrimaryButton
            {
                anchors.right: parent.right
                text: catalog.i18nc("@action:button", "OK")
                onClicked:
                {
                    manager.setSendSliceInfo(allowSendData)
                    baseDialog.hide()
                }
            }

            Cura.SecondaryButton
            {
                anchors.left: parent.left
                text: catalog.i18nc("@action:button", "Cancel")
                onClicked:
                {
                    baseDialog.hide()
                }
            }
        }
    }
}
