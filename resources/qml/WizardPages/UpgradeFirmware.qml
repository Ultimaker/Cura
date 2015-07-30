// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

ColumnLayout {
    property string title
    anchors.fill: parent;
    signal openFile(string fileName)

    Label {
        text: parent.title
        font.pointSize: 18;
    }

    Label {
        //: Add Printer wizard page description
        text: qsTr("Please select the type of printer:");
    }

    ScrollView {
        Layout.fillWidth: true;

        ListView {
            id: machineList;
            model: UM.Models.availableMachinesModel
            delegate: RadioButton {
                exclusiveGroup: printerGroup;
                text: model.name;
                onClicked: {
                    ListView.view.currentIndex = index;
                }
            }
        }
    }

    Label {
        //: Add Printer wizard field label
        text: qsTr("Printer Name:");
    }

    TextField { id: machineName; Layout.fillWidth: true; text: machineList.model.getItem(machineList.currentIndex).name }

    Item { Layout.fillWidth: true; Layout.fillHeight: true; }

    ExclusiveGroup { id: printerGroup; }
}