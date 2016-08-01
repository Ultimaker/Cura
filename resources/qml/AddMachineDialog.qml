// Copyright (c) 2016 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import QtQuick.Controls.Styles 1.1

import UM 1.2 as UM
import Cura 1.0 as Cura


UM.Dialog
{
    id: base
    title: catalog.i18nc("@title:window", "Add Printer")
    property bool firstRun: false
    property string preferredCategory: "Ultimaker"
    property string activeCategory: preferredCategory

    onVisibilityChanged:
    {
        // Reset selection and machine name
        if (visible) {
            activeCategory = preferredCategory;
            machineList.currentIndex = 0;
            machineName.text = getMachineName();
        }
    }

    signal machineAdded(string id)
    function getMachineName()
    {
        var name = machineList.model.get(machineList.currentIndex) != undefined ? machineList.model.get(machineList.currentIndex).name : ""
        return name
    }

    ScrollView
    {
        id: machinesHolder

        anchors
        {
            left: parent.left;
            top: parent.top;
            right: parent.right;
            bottom: parent.bottom;
        }

        ListView
        {
            id: machineList

            model: ListModel
            {
                id: sortedMachineDefinitionsModel
                Component.onCompleted: {
                    // DefinitionContainersModel is sorted alphabetically, but we want the preferred
                    // category on top so we create a custom-sorted ListModel from it.
                    var items = [];
                    for(var i in machineDefinitionsModel.items) {
                        var item = machineDefinitionsModel.getItem(i);
                        if (item["category"] == preferredCategory)
                            sortedMachineDefinitionsModel.append(item);
                        else
                            items.push(item);
                    }
                    for(var i in items) {
                        sortedMachineDefinitionsModel.append(items[i]);
                    }
                }
            }

            section.property: "category"
            section.delegate: Button
            {
                text: section
                style: ButtonStyle
                {
                    background: Rectangle
                    {
                        border.width: 0
                        color: "transparent";
                        height: UM.Theme.getSize("standard_list_lineheight").height
                        width: machineList.width
                    }
                    label: Label
                    {
                        anchors.left: parent.left
                        anchors.leftMargin: UM.Theme.getSize("standard_arrow").width + UM.Theme.getSize("default_margin").width
                        text: control.text
                        color: palette.windowText
                        font.bold: true
                        UM.RecolorImage
                        {
                            id: downArrow
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.right: parent.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            width: UM.Theme.getSize("standard_arrow").width
                            height: UM.Theme.getSize("standard_arrow").height
                            sourceSize.width: width
                            sourceSize.height: width
                            color: palette.windowText
                            source: base.activeCategory == section ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_right")
                        }
                    }
                }

                onClicked:
                {
                    base.activeCategory = section;
                    if (machineList.model.get(machineList.currentIndex).category != section) {
                        // Find the first machine from this category
                        for(var i = 0; i < sortedMachineDefinitionsModel.count; i++) {
                            var item = sortedMachineDefinitionsModel.get(i);
                            if (item.category == section) {
                                machineList.currentIndex = i;
                                break;
                            }
                        }
                    }
                    machineName.text = getMachineName();
                }
            }

            delegate: RadioButton
            {
                id: machineButton

                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("standard_list_lineheight").width

                opacity: 1;
                height: UM.Theme.getSize("standard_list_lineheight").height;

                checked: ListView.isCurrentItem;

                exclusiveGroup: printerGroup;

                text: model.name

                onClicked:
                {
                    ListView.view.currentIndex = index;
                    machineName.text = getMachineName()
                }

                states: State
                {
                    name: "collapsed";
                    when: base.activeCategory != model.category;

                    PropertyChanges { target: machineButton; opacity: 0; height: 0; }
                }

                transitions:
                [
                    Transition
                    {
                        to: "collapsed";
                        SequentialAnimation
                        {
                            NumberAnimation { property: "opacity"; duration: 75; }
                            NumberAnimation { property: "height"; duration: 75; }
                        }
                    },
                    Transition
                    {
                        from: "collapsed";
                        SequentialAnimation
                        {
                            NumberAnimation { property: "height"; duration: 75; }
                            NumberAnimation { property: "opacity"; duration: 75; }
                        }
                    }
                ]
            }
        }
    }

    TextField
    {
        id: machineName;
        text: getMachineName()
        implicitWidth: UM.Theme.getSize("standard_list_input").width
        maximumLength: 40
        anchors.bottom:parent.bottom
    }

    Button
    {
        text: catalog.i18nc("@action:button", "Add Printer")
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        onClicked:
        {
            base.visible = false
            var item = machineList.model.get(machineList.currentIndex);
            Cura.MachineManager.addMachine(machineName.text, item.id)
            base.machineAdded(item.id) // Emit signal that the user added a machine.
        }
    }

    Item
    {
        UM.I18nCatalog
        {
            id: catalog;
            name: "cura";
        }
        UM.DefinitionContainersModel
        {
            id: machineDefinitionsModel
            filter: { "visible": true }
        }
        SystemPalette { id: palette }
        ExclusiveGroup { id: printerGroup; }
    }
}
