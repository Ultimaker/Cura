import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

Window {
    id: base

    width: 640
    height: 480

    //: Add Printer dialog title
    title: qsTr("Add Printer");

    Rectangle {
        anchors.fill: parent;
        color: palette.window;

        ColumnLayout {
            anchors.fill: parent;
            anchors.margins: UM.Theme.defaultMargin;

            Label {
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
                text: qsTr("Printer Name:");
            }

            TextField { id: machineName; Layout.fillWidth: true; text: machineList.model.getItem(machineList.currentIndex).name }

            Item { Layout.fillWidth: true; Layout.fillHeight: true; }

            ExclusiveGroup { id: printerGroup; }

            RowLayout {
                Layout.fillWidth: true

                Item { Layout.fillWidth: true; }

                Button {
                    text: qsTr("Next");
                    onClicked: {
                        if(machineList.currentIndex != -1) {
                            UM.Models.availableMachinesModel.createMachine(machineList.currentIndex, machineName.text)
                            base.visible = false
                        }
                    }
                }

                Button {
                    text: qsTr("Cancel");
                    onClicked: base.visible = false;
                }
            }
        }
    }

    SystemPalette { id: palette; colorGroup: SystemPalette.Active }
}
