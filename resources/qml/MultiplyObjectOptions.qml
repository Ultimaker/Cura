// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    id: base

    //: Dialog title
    title: catalog.i18nc("@title:window", "Multiply Model")

    minimumWidth: 400 * Screen.devicePixelRatio
    minimumHeight: 80 * Screen.devicePixelRatio
    width: minimumWidth
    height: minimumHeight

    property var objectId: 0;
    onAccepted: Printer.multiplyObject(base.objectId, parseInt(copiesField.text))

    property variant catalog: UM.I18nCatalog { name: "cura" }

    signal reset()
    onReset: {
        copiesField.text = "1";
        copiesField.selectAll();
        copiesField.focus = true;
    }

    Row
    {
        spacing: UM.Theme.getSize("default_margin").width

        Label {
            text: "Number of copies:"
            anchors.verticalCenter: copiesField.verticalCenter
        }

        TextField {
            id: copiesField
            validator: RegExpValidator { regExp: /^\d{0,2}/ }
            maximumLength: 2
        }
    }


    rightButtons:
    [
        Button
        {
            text: catalog.i18nc("@action:button","OK")
            onClicked: base.accept()
            enabled: base.objectId != 0 && parseInt(copiesField.text) > 0
        },
        Button
        {
            text: catalog.i18nc("@action:button","Cancel")
            onClicked: base.reject()
        }
    ]
}

