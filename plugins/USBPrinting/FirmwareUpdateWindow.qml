// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Window 2.2
import QtQuick.Controls 1.2

import UM 1.1 as UM

UM.Dialog
{
    id: base;

    width: 500 * Screen.devicePixelRatio;
    height: 100 * Screen.devicePixelRatio;

    visible: true;
    modality: Qt.ApplicationModal;

    title: catalog.i18nc("@title:window","Firmware Update");

    Column
    {
        anchors.fill: parent;

        Label
        {
            anchors
            {
                left: parent.left;
                right: parent.right;
            }

            text: {
                if (manager.firmwareUpdateCompleteStatus)
                {
                    //: Firmware update status label
                    return catalog.i18nc("@label","Firmware update completed.")
                }
                else if (manager.progress == 0)
                {
                    //: Firmware update status label
                    return catalog.i18nc("@label","Starting firmware update, this may take a while.")
                }
                else
                {
                    //: Firmware update status label
                    return catalog.i18nc("@label","Updating firmware.")
                }
            }

            wrapMode: Text.Wrap;
        }

        ProgressBar
        {
            id: prog
            value: manager.firmwareUpdateCompleteStatus ? 100 : manager.progress
            minimumValue: 0
            maximumValue: 100
            indeterminate: (manager.progress < 1) && (!manager.firmwareUpdateCompleteStatus)
            anchors
            {
                left: parent.left;
                right: parent.right;
            }

        }

        SystemPalette
        {
           id: palette;
        }

        UM.I18nCatalog { id: catalog; name: "cura"; }
    }

    rightButtons: [
        Button
        {
            text: catalog.i18nc("@action:button","Close");
            enabled: manager.firmwareUpdateCompleteStatus;
            onClicked: base.visible = false;
        }
    ]
}
