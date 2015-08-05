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
        ListView {
            id: machineList;
            model: UM.Models.availableMachinesModel
            delegate: RadioButton {
                id:machine_button
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
        text: qsTr("Variation:");
        }

    ScrollView {
        ListView {
            id: variations_list
            model: machineList.model.getItem(machineList.currentIndex).variations
            delegate: RadioButton {
                id: variation_radio_button
                checked: ListView.view.currentIndex == index ? true : false
                exclusiveGroup: variationGroup;
                text: model.name;
                onClicked: ListView.view.currentIndex = index;
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
    ExclusiveGroup { id: variationGroup; }

    function getSpecialMachineType(machineId){
        for (var i = 0; i < UM.Models.addMachinesModel.rowCount(); i++) {
            if (UM.Models.addMachinesModel.getItem(i).name == machineId){
               return UM.Models.addMachinesModel.getItem(i).name
            }
        }
    }

    function saveMachine(){
        if(machineList.currentIndex != -1) {
            UM.Models.availableMachinesModel.createMachine(machineList.currentIndex, variations_list.currentIndex, machineName.text)

            var originalString = "Ultimaker Original"
            var originalPlusString = "Ultimaker Original+"
            var originalMachineType = getSpecialMachineType(originalString)

            if (UM.Models.availableMachinesModel.getItem(machineList.currentIndex).name == originalMachineType){
                var variation = UM.Models.availableMachinesModel.getItem(machineList.currentIndex).variations.getItem(variations_list.currentIndex).name
                if (variation == originalString || variation == originalPlusString){
                    console.log(UM.Models.availableMachinesModel.getItem(machineList.currentIndex).variations.getItem(variations_list.currentIndex).type)
                    wizardPage.openFile(UM.Models.availableMachinesModel.getItem(machineList.currentIndex).variations.getItem(variations_list.currentIndex).type)
                }
            }
            else {
                wizardPage.closeWizard()
            }
        }
    }
}

