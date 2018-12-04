// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

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

    minimumWidth: UM.Theme.getSize("modal_window_minimum").width
    minimumHeight: UM.Theme.getSize("modal_window_minimum").height
    width: minimumWidth
    height: minimumHeight

    flags:
    {
        var window_flags = Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint;
        if (Cura.MachineManager.activeDefinitionId !== "") //Disallow closing the window if we have no active printer yet. You MUST add a printer.
        {
            window_flags |= Qt.WindowCloseButtonHint;
        }
        return window_flags;
    }

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
        if (machineList.model.getItem(machineList.currentIndex) != undefined)
        {
            return machineList.model.getItem(machineList.currentIndex).name;
        }
        return  "";
    }

    function getMachineMetaDataEntry(key)
    {
        if (machineList.model.getItem(machineList.currentIndex) != undefined)
        {
            return machineList.model.getItem(machineList.currentIndex).metadata[key];
        }
        return  "";
    }

    Label
    {
        id: titleLabel

        anchors
        {
            top: parent.top
            left: parent.left
            topMargin: UM.Theme.getSize("default_margin").height
        }
        text: catalog.i18nc("@title:tab", "Add a printer to Cura")

        font.pointSize: 18
    }

    Label
    {
        id: captionLabel
        anchors
        {
            left: parent.left
            top: titleLabel.bottom
            topMargin: UM.Theme.getSize("default_margin").height
        }
        text: catalog.i18nc("@title:tab", "Select the printer you want to use from the list below.\n\nIf your printer is not in the list, use the \"Custom FFF Printer\" from the \"Custom\" category and adjust the settings to match your printer in the next dialog.")
        width: parent.width
        wrapMode: Text.WordWrap
    }

    ScrollView
    {
        id: machinesHolder

        anchors
        {
            top: captionLabel.visible ? captionLabel.bottom : parent.top;
            topMargin: captionLabel.visible ? UM.Theme.getSize("default_margin").height : 0;
            bottom: addPrinterButton.top;
            bottomMargin: UM.Theme.getSize("default_margin").height
        }

        width: Math.round(parent.width * 0.45)

        frameVisible: true;
        Rectangle
        {
            parent: viewport
            anchors.fill: parent
            color: palette.light
        }

        ListView
        {
            id: machineList

            model: UM.DefinitionContainersModel
            {
                id: machineDefinitionsModel
                filter: { "visible": true }
                sectionProperty: "category"
                preferredSectionValue: preferredCategory
            }

            section.property: "section"
            section.delegate: Button
            {
                id: machineSectionButton
                text: section
                width: machineList.width
                style: ButtonStyle
                {
                    background: Item
                    {
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
                            sourceSize.height: width
                            color: palette.windowText
                            source: base.activeCategory == section ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_right")
                        }
                    }
                }

                onClicked:
                {
                    base.activeCategory = section;
                    if (machineList.model.getItem(machineList.currentIndex).section != section)
                    {
                        // Find the first machine from this section
                        for(var i = 0; i < machineList.model.count; i++)
                        {
                            var item = machineList.model.getItem(i);
                            if (item.section == section)
                            {
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
                    when: base.activeCategory != model.section;

                    PropertyChanges { target: machineButton; opacity: 0; height: 0; }
                }
            }
        }
    }

    Column
    {
        anchors
        {
            top: machinesHolder.top
            left: machinesHolder.right
            right: parent.right
            leftMargin: UM.Theme.getSize("default_margin").width
        }

        spacing: UM.Theme.getSize("default_margin").height
        Label
        {
            width: parent.width
            wrapMode: Text.WordWrap
            text: getMachineName()
            font.pointSize: 16
            elide: Text.ElideRight
        }
        Grid
        {
            width: parent.width
            columns: 2
            rowSpacing: UM.Theme.getSize("default_lining").height
            columnSpacing: UM.Theme.getSize("default_margin").width
            verticalItemAlignment: Grid.AlignVCenter

            Label
            {
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label", "Manufacturer")
            }
            Label
            {
                width: Math.floor(parent.width * 0.65)
                wrapMode: Text.WordWrap
                text: getMachineMetaDataEntry("manufacturer")
            }
            Label
            {
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label", "Author")
            }
            Label
            {
                width: Math.floor(parent.width * 0.75)
                wrapMode: Text.WordWrap
                text: getMachineMetaDataEntry("author")
            }
            Label
            {
                wrapMode: Text.WordWrap
                text: catalog.i18nc("@label", "Printer Name")
            }
            TextField
            {
                id: machineName
                text: getMachineName()
                width: Math.floor(parent.width * 0.75)
                maximumLength: 40
                //validator: Cura.MachineNameValidator { } //TODO: Gives a segfault in PyQt5.6. For now, we must use a signal on text changed.
                validator: RegExpValidator
                {
                    regExp: {
                        machineName.machine_name_validator.machineNameRegex
                    }
                }
                property var machine_name_validator: Cura.MachineNameValidator { }
            }
        }
    }

    Button
    {
        id: addPrinterButton
        text: catalog.i18nc("@action:button", "Add Printer")
        anchors.bottom: parent.bottom
        anchors.right: parent.right
        onClicked: addMachine()
    }

    onAccepted: addMachine()

    function addMachine()
    {
        base.visible = false
        var item = machineList.model.getItem(machineList.currentIndex);
        Cura.MachineManager.addMachine(machineName.text, item.id)
        base.machineAdded(item.id) // Emit signal that the user added a machine.
    }

    Item
    {
        UM.I18nCatalog
        {
            id: catalog;
            name: "cura";
        }
        SystemPalette { id: palette }
        ExclusiveGroup { id: printerGroup; }
    }
}
