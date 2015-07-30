// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM
import ".."

ColumnLayout {
    id: wizardPage
    property string title
    anchors.fill: parent
    signal openFile(string fileName)
    signal closeWizard()

    Connections {
        target: rootElement
        onFinalClicked: {//You can add functions here that get triggered when the final button is clicked in the wizard-element
            saveMachine()
        }
    }

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
                checked: ListView.view.currentIndex == index ? true : false
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

    function getSpecialMachineType(machineId){
        for (var i = 0; i < UM.Models.addMachinesModel.rowCount(); i++) {
            if (UM.Models.addMachinesModel.getItem(i).id == machineId){
               return UM.Models.addMachinesModel.getItem(i).file
            }
        }
    }

    function saveMachine(){
        if(machineList.currentIndex != -1) {
            UM.Models.availableMachinesModel.createMachine(machineList.currentIndex, machineName.text)

            var chosenMachineType = UM.Models.availableMachinesModel.getItem(machineList.currentIndex).type
            var originalMachineType = getSpecialMachineType("ultimaker_original")
            var orginalPlusMachineType = getSpecialMachineType("ultimaker_original_plus")

            if (chosenMachineType == originalMachineType)
                wizardPage.openFile(originalMachineType)
            if (chosenMachineType == orginalPlusMachineType)
                wizardPage.openFile(orginalPlusMachineType)
            else
                wizardPage.closeWizard()
        }
    }
}

