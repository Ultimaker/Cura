// Copyright (c) 2015 Ultimaker B.V.
// Uranium is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1
import QtQuick.Controls.Styles 1.1
import QtQml 2.2

import UM 1.1 as UM

import "../Preferences"

PreferencesPage
{
    //: Machine configuration page title.
    title: catalog.i18nc("@title:tab","Machine");
    id: base

    contents: ColumnLayout
    {
        z: base.z
        anchors.fill: parent;
        UM.I18nCatalog { id: catalog; name:"uranium"}
        RowLayout
        {
            //: Active machine combo box label
            Label { text: catalog.i18nc("@label:listbox","Active Machine:"); }
            ComboBox
            {
                id: machineCombo;
                Layout.fillWidth: true;
                model: UM.Models.machinesModel;
                textRole: "name";
                onActivated:
                {
                    if(index != -1)
                        UM.Models.machinesModel.setActive(index);
                }

                Connections
                {
                    id: machineChange
                    target: UM.Application
                    onMachineChanged: machineCombo.currentIndex = machineCombo.find(UM.Application.machineName);
                }

                Component.onCompleted: machineCombo.currentIndex = machineCombo.find(UM.Application.machineName);
            }
            //: Remove active machine button
            Button { text: catalog.i18nc("@action:button","Remove"); onClicked: confirmRemoveDialog.open(); }
        }
        ScrollView
        {
            id: settingsScrollView
            Layout.fillWidth: true;
            Layout.fillHeight: true;

            ListView
            {
                id: settingsListView
                delegate: settingDelegate
                model: UM.Models.settingsModel
                x: 0

                section.property: "category"
                section.delegate: Label { text: section }
            }
        }
    }

    Component
    {
        id: settingDelegate
        CheckBox
        {
            z:0
            id: settingCheckBox
            text: model.name;
            x: depth * 25
            checked: model.visibility
            onClicked: ListView.view.model.setVisibility(model.key, checked)
            //enabled: !model.disabled

            onHoveredChanged:
            {
                if(hovered)
                {
                    var xPos = parent.x + settingCheckBox.width;
                    var yPos = parent.y;
                    toolTip.show(model.description, 1000, 200, undefined, undefined) //tooltip-text, hover-delay in msec, animation-length in msec, position X, position Y (both y en x == undefined: gives the tooltip a standard placement in the right corner)
                } else
                {
                    toolTip.hide(0, 0)//hover-delay in msec, animation-length in msec
                }
            }
        }
    }

    PreferencesToolTip
    {
        id: toolTip;
    }

    MessageDialog
    {
        id: confirmRemoveDialog;

        icon: StandardIcon.Question;
        //: Remove machine confirmation dialog title
        title: catalog.i18nc("@title:window","Confirm Machine Deletion");
        //: Remove machine confirmation dialog text
        text: catalog.i18nc("@label","Are you sure you wish to remove the machine?");
        standardButtons: StandardButton.Yes | StandardButton.No;

        onYes: UM.Models.machinesModel.removeMachine(machineCombo.currentIndex);
    }
}
