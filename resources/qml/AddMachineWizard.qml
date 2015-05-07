import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

UM.Dialog {
    id: base

    //: Add Printer dialog title
    title: qsTr("Add Printer");

    ColumnLayout {
        anchors.fill: parent;

        Label {
            //: Add Printer wizard page title
            text: qsTr("Add Printer");
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
                delegate: RadioButton { exclusiveGroup: printerGroup; text: model.name; onClicked: ListView.view.currentIndex = index; }
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

    rightButtons: [
        Button {
            //: Add Printer wizarad button
            text: qsTr("Next");
            onClicked: {
                if(machineList.currentIndex != -1) {
                    UM.Models.availableMachinesModel.createMachine(machineList.currentIndex, machineName.text)
                    base.visible = false
                }
            }
        },
        Button {
            //: Add Printer wizarad button
            text: qsTr("Cancel");
            onClicked: base.visible = false;
        }
    ]
}
