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

    buttonSpacing: UM.Theme.getSize("default_margin").width

    property string object: ""
    property string objectPlaceholder: ""

    property alias newName: nameField.text
    property bool validName: true
    property string validationError
    property string dialogTitle: catalog.i18nc("@title:window", "Rename")
    property string explanation: catalog.i18nc("@info", "Please provide a new name.")
    property string okButtonText: catalog.i18nc("@action:button", "OK")

    // Extra Information for the user about the current rename can go here, can be left alone if not needed.
    // For example; An icon and a text-field and a tertiary button providing a link.
    property list<Item> extraInfo

    title: dialogTitle
    backgroundColor: UM.Theme.getColor("main_background")
    minimumWidth: UM.Theme.getSize("small_popup_dialog").width
    minimumHeight: UM.Theme.getSize("small_popup_dialog").height + extraInfoHolder.height
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
            placeholderText: base.objectPlaceholder
            placeholderTextColor: UM.Theme.getColor("text_field_text_disabled")
            maximumLength: 40
            selectByMouse: true
            onTextChanged: base.textChanged(text)
        }

        // spacer
        Item
        {
            height: UM.Theme.getSize("wide_margin").height
            width: height
        }

        Row
        {
            id: extraInfoHolder
            anchors
            {
                left: parent.left
                right: parent.right
                margins: UM.Theme.getSize("default_margin").height
            }
            spacing: UM.Theme.getSize("default_margin").height
            children: extraInfo
        }

        UM.Label
        {
            visible: !base.validName
            text: base.validationError
        }
    }

    leftButtons:
    [
        Cura.TertiaryButton
        {
            id: cancelButton
            text: catalog.i18nc("@action:button","Cancel")
            onClicked: base.reject()
        }
    ]
    rightButtons:
    [
        Cura.PrimaryButton
        {
            id: okButton
            text: base.okButtonText
            onClicked: base.accept()
            enabled: base.validName
        }
    ]
}
