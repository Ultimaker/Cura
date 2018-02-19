// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Window 2.2
import QtQuick.Controls 1.2

import UM 1.1 as UM

UM.Dialog
{
    id: base;

    width: minimumWidth;
    minimumWidth: 500 * screenScaleFactor;
    height: minimumHeight;
    minimumHeight: 100 * screenScaleFactor;

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
                switch (manager.firmwareUpdateState)
                {
                    case 0:
                        return "" //Not doing anything (eg; idling)
                    case 1:
                        return catalog.i18nc("@label","Updating firmware.")
                    case 2:
                        return catalog.i18nc("@label","Firmware update completed.")
                    case 3:
                        return catalog.i18nc("@label","Firmware update failed due to an unknown error.")
                    case 4:
                        return catalog.i18nc("@label","Firmware update failed due to an communication error.")
                    case 5:
                        return catalog.i18nc("@label","Firmware update failed due to an input/output error.")
                    case 6:
                        return catalog.i18nc("@label","Firmware update failed due to missing firmware.")
                }
            }

            wrapMode: Text.Wrap;
        }

        ProgressBar
        {
            id: prog
            value: manager.firmwareProgress
            minimumValue: 0
            maximumValue: 100
            indeterminate: manager.firmwareProgress < 1 && manager.firmwareProgress > 0
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
