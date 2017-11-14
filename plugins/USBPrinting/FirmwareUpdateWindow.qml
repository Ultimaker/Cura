// Copyright (c) 2015 Ultimaker B.V.
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
                if (manager.errorCode == 0)
                {
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
                else
                {
                    switch (manager.errorCode)
                    {
                        case 1:
                            //: Firmware update status label
                            return catalog.i18nc("@label","Firmware update failed due to an unknown error.")
                        case 2:
                            //: Firmware update status label
                            return catalog.i18nc("@label","Firmware update failed due to an communication error.")
                        case 3:
                            //: Firmware update status label
                            return catalog.i18nc("@label","Firmware update failed due to an input/output error.")
                        case 4:
                            //: Firmware update status label
                            return catalog.i18nc("@label","Firmware update failed due to missing firmware.")
                        default:
                            //: Firmware update status label
                            return catalog.i18nc("@label", "Unknown error code: %1").arg(manager.errorCode)
                    }
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
