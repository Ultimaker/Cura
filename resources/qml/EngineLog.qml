// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1

import UM 1.1 as UM

UM.Dialog
{
    id: dialog;

    //: Engine Log dialog title
    title: catalog.i18nc("@title:window","Engine Log");

    modality: Qt.NonModal;

    TextArea
    {
        id: textArea
        anchors.fill: parent;

        Timer
        {
            id: updateTimer;
            interval: 1000;
            running: false;
            repeat: true;
            onTriggered: textArea.text = CuraApplication.getEngineLog();
        }
        UM.I18nCatalog{id: catalog; name:"cura"}
    }

    rightButtons: Button
    {
        //: Close engine log button
        text: catalog.i18nc("@action:button","Close");
        onClicked: dialog.visible = false;
    }

    onVisibleChanged:
    {
        if(visible)
        {
            textArea.text = CuraApplication.getEngineLog();
            updateTimer.start();
        } else
        {
            updateTimer.stop();
        }
    }
}
