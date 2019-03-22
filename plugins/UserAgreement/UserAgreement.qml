// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.4

import UM 1.3 as UM

UM.Dialog
{
    id: baseDialog
    minimumWidth: Math.round(UM.Theme.getSize("modal_window_minimum").width * 0.75)
    minimumHeight: Math.round(UM.Theme.getSize("modal_window_minimum").height * 0.5)
    width: minimumWidth
    height: minimumHeight
    title: catalog.i18nc("@title:window", "User Agreement")

    TextArea
    {
        anchors.top: parent.top
        width: parent.width
        anchors.bottom: buttonRow.top
        text: ' <center><h3>DISCLAIMER BY ULTIMAKER</h3></center>
                <p>PLEASE READ THIS DISCLAIMER CAREFULLY.</p>
                <p>EXCEPT WHEN OTHERWISE STATED IN WRITING, ULTIMAKER PROVIDES ANY ULTIMAKER SOFTWARE OR THIRD PARTY SOFTWARE “AS IS” WITHOUT WARRANTY OF ANY KIND. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF ULTIMAKER SOFTWARE IS WITH YOU.</p>
                <p>UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING, IN NO EVENT WILL ULTIMAKER BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE ANY ULTIMAKER SOFTWARE OR THIRD PARTY SOFTWARE.</p>
                '
        readOnly: true;
        textFormat: TextEdit.RichText
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
            text: catalog.i18nc("@action:button", "I understand and agree")
            onClicked: {
                baseDialog.accepted()
            }
        }

        Button
        {
            anchors.left: parent.left
            text: catalog.i18nc("@action:button", "I don't agree")
            onClicked: {
                baseDialog.rejected()
            }
        }
    }

    onAccepted: manager.didAgree(true)
    onRejected: manager.didAgree(false)
    onClosing: manager.didAgree(false)
}
