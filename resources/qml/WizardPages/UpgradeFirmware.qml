// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

Column
{
    id: wizardPage
    property string title
    anchors.fill: parent;
    Label
    {
        text: parent.title
        font.pointSize: 18;
    }

    ScrollView
    {
        height: parent.height - 50
        width: parent.width
        ListView
        {
            id: machineList;
            model: UM.USBPrinterManager.connectedPrinterList

            delegate:Row
            {
                id: derp
                Text
                {
                    id: text_area
                    text: model.name
                }
                Button
                {
                    text: "Update";
                    onClicked:
                    {
                        if(!UM.USBPrinterManager.updateFirmwareBySerial(text_area.text))
                        {
                            status_text.text = "ERROR"
                        }
                    }
                }
            }
        }
    }

    Label
    {
        id: status_text
        text: ""
    }


    Item
    {
        Layout.fillWidth: true;
        Layout.fillHeight: true;
    }


}