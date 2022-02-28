// Copyright (c) 2022 Ultimaker B.V.
// Uranium is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 2.0
import QtQuick.Window 2.1

import UM 1.5 as UM
import Cura 1.0 as Cura

UM.Dialog
{
    id: base
    property string object: ""

    property alias newName: nameField.text
    property bool validName: true
    property string validationError
    property string dialogTitle: catalog.i18nc("@title:window", "Rename")
    property string explanation: catalog.i18nc("@info", "Please provide a new name.")

    title: dialogTitle

    minimumWidth: UM.Theme.getSize("small_popup_dialog").width
    minimumHeight: UM.Theme.getSize("small_popup_dialog").height
    width: minimumWidth
    height: minimumHeight

    property variant catalog: UM.I18nCatalog { name: "cura" }

    signal textChanged(string text)
    signal selectText()
    onSelectText:
    {
        nameField.selectAll();
        nameField.focus = true;
    }

    Column
    {
        anchors.fill: parent

        UM.Label
        {
            text: base.explanation + "\n" //Newline to make some space using system theming.
            width: parent.width
            wrapMode: Text.WordWrap
        }

        Cura.TextField
        {
            id: nameField
            width: parent.width
            text: base.object
            maximumLength: 40
            selectByMouse: true
            onTextChanged: base.textChanged(text)
        }

        UM.Label
        {
            visible: !base.validName
            text: base.validationError
        }
    }

    Item
    {
        ButtonGroup {
            buttons: [cancelButton, okButton]
            checkedButton: okButton
        }
    }

    rightButtons: [
        Cura.SecondaryButton
        {
            id: cancelButton
            text: catalog.i18nc("@action:button","Cancel")
            onClicked: base.reject()
        },
        Cura.PrimaryButton
        {
            id: okButton
            text: catalog.i18nc("@action:button", "OK")
            onClicked: base.accept()
            enabled: base.validName
        }
    ]
}

