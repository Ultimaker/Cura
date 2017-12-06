// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.3
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    id: base
    minimumWidth: (UM.Theme.getSize("modal_window_minimum").width * 0.75) | 0
    minimumHeight: (UM.Theme.getSize("modal_window_minimum").height * 0.75) | 0
    width: minimumWidth
    height: minimumHeight
    title: catalog.i18nc("@label", "Changelog")

    TextArea
    {
        anchors.fill: parent
        text: manager.getChangeLogString()
        readOnly: true;
        textFormat: TextEdit.RichText
    }

    rightButtons: [
        Button
        {
            UM.I18nCatalog
            {
                id: catalog
                name: "cura"
            }

            text: catalog.i18nc("@action:button", "Close")
            onClicked: base.hide()
        }
    ]
}
