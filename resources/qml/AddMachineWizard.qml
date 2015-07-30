// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.0 as UM

UM.Dialog 
{
    id: base

    //: Add Printer dialog title
    title: qsTr("Add Printer");

    ColumnLayout 
    {
        anchors.fill: parent;

        Label 
        {
            //: Add Printer wizard page title
            text: qsTr("Add Printer");
            font.pointSize: 18;
        }

        Label 
        {
            //: Add Printer wizard page description
            text: qsTr("Please select the type of printer:");
        }

        ScrollView 
        {
            Layout.fillWidth: true;

            ListView 
            {
                id: machineList;
                model: UM.Models.availableMachinesModel
                delegate: RadioButton 
                { 
                    id:machine_button
                    exclusiveGroup: printerGroup; 
                    text: model.name; 
                    onClicked: ListView.view.currentIndex = index; 
                    Component.onCompleted: 
                    {
                        if(index == 0)
                        {
                            machine_button.checked = true
                            ListView.view.currentIndex = index; 
                        }
                    }
                }
            }
        }
        Label 
        {
            text: qsTr("Variation:");
        }
        
        ScrollView
        {
            width: 50
            height:150
            
            ListView 
            {
                Component.onCompleted:console.log(model)
                id: variations_list
                model: machineList.model.getItem(machineList.currentIndex).variations
                delegate: RadioButton 
                { 
                    id: variation_radio_button
                    exclusiveGroup: variationGroup; 
                    text: model.name; 
                    onClicked: ListView.view.currentIndex = index; 
                    Component.onCompleted: 
                    {
                        if(index == 0)
                        {
                            variation_radio_button.checked = true
                            ListView.view.currentIndex = index; 
                        }
                    }
                }  
            }
            
        }
        Label 
        {
            //: Add Printer wizard field label
            text: qsTr("Printer Name:");
        }
        TextField { id: machineName; Layout.fillWidth: true; text: machineList.model.getItem(machineList.currentIndex).variations.getItem(variations_list.currentIndex).name }

        Item { Layout.fillWidth: true; Layout.fillHeight: true; }

        ExclusiveGroup { id: printerGroup; }
        ExclusiveGroup { id: variationGroup; }
    }

    rightButtons: [
        Button 
        {
            //: Add Printer wizarad button
            text: qsTr("Next");
            onClicked: 
            {
                if(machineList.currentIndex != -1) 
                {
                    UM.Models.availableMachinesModel.createMachine(machineList.currentIndex, variations_list.currentIndex, machineName.text)
                    base.visible = false
                }
            }
        },
        Button 
        {
            //: Add Printer wizarad button
            text: qsTr("Cancel");
            onClicked: base.visible = false;
        }
    ]
}
