// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
Rectangle 
{
    width: 300; height: 100
    ColumnLayout 
    {

        Text 
        {
            text: {
                if (manager.progress == 0)
                {
                    //: Firmware update status label
                    return qsTr("Starting firmware update, this may take a while.")
                }
                else if (manager.progress > 99)
                {
                    //: Firmware update status label
                    return qsTr("Firmware update completed.")
                }
                else
                {
                    //: Firmware update status label
                    return qsTr("Updating firmware.")
                }
            }
        }
        ProgressBar 
        {
            id: prog;
            value: manager.progress
            minimumValue: 0;
            maximumValue: 100;
            Layout.maximumWidth:parent.width
            Layout.preferredWidth:230
            Layout.preferredHeight:25
            Layout.minimumWidth:230
            Layout.minimumHeight:25
            width: 230
            height: 25
        }
    }
}
