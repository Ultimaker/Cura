// Copyright (c) 2023 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.15
import QtQuick.Controls 2.14

import UM 1.5 as UM
import Cura 1.1 as Cura


//
// This is the scroll view widget for adding a (local) printer. This scroll view shows a list view with printers
// categorized into 3 categories: "Ultimaker", "Custom", and "Other".
//
Item
{
    id: base

    // The currently selected machine item in the local machine list.
    property var currentItem: machineList.currentIndex >= 0 ? machineList.model.getItem(machineList.currentIndex) : null
    // The currently active (expanded) section/category, where section/category is the grouping of local machine items.
    property var currentSections: new Set()
    // By default (when this list shows up) we always expand the "Ultimaker" section.
    property var preferredCategories: {
        "Ultimaker B.V.": -2,
        "Custom": -1
    }

    // User-editable printer name
    property alias printerName: printerNameTextField.text
    property alias isPrinterNameValid: printerNameTextField.acceptableInput

    onCurrentItemChanged:
    {
        printerName = currentItem == null ? "" : currentItem.name
    }

    function updateCurrentItemUponSectionChange(section)
    {
        // Find the first machine from this section
        for (var i = 0; i < machineList.count; i ++)
        {
            const item = machineList.model.getItem(i);
            if (item.section == section)
            {
                machineList.currentIndex = i;
                break;
            }
        }
    }

    function getMachineName()
    {
        return machineList.model.getItem(machineList.currentIndex) != undefined ? machineList.model.getItem(machineList.currentIndex).name : "";
    }

    function getMachineMetaDataEntry(key)
    {
        var metadata = machineList.model.getItem(machineList.currentIndex) != undefined ? machineList.model.getItem(machineList.currentIndex).metadata : undefined;
        if (metadata)
        {
            return metadata[key];
        }
        return undefined;
    }

    Component.onCompleted:
    {
        const initialSection = "Ultimaker B.V.";
        base.currentSections.add(initialSection);
        updateCurrentItemUponSectionChange(initialSection);
        // Trigger update on base.currentSections
        base.currentSections = base.currentSections;
    }

    Row
    {
        id: localPrinterSelectionItem
        anchors.fill: parent

        //Selecting a local printer to add from this list.
        ListView
        {
            id: machineList
            width: Math.floor(parent.width * 0.48)
            height: parent.height

            clip: true
            ScrollBar.vertical: UM.ScrollBar {}

            model: UM.DefinitionContainersModel
            {
                id: machineDefinitionsModel
                filter: { "visible": true }
                sectionProperty: "manufacturer"
                preferredSections: preferredCategories
            }

            section.property: "section"
            section.delegate: Button
            {
                id: button
                width: machineList.width
                height: UM.Theme.getSize("action_button").height
                text: section

                property bool isActive: base.currentSections.has(section)

                background: Rectangle
                {
                    anchors.fill: parent
                    color: isActive ? UM.Theme.getColor("setting_control_highlight") : "transparent"
                }

                contentItem: Item
                {
                    width: childrenRect.width
                    height: UM.Theme.getSize("action_button").height

                    UM.ColorImage
                    {
                        id: arrow
                        anchors.left: parent.left
                        width: UM.Theme.getSize("standard_arrow").width
                        height: UM.Theme.getSize("standard_arrow").height
                        color: UM.Theme.getColor("text")
                        source: isActive ? UM.Theme.getIcon("ChevronSingleDown") : UM.Theme.getIcon("ChevronSingleRight")
                    }

                    UM.Label
                    {
                        id: label
                        anchors.left: arrow.right
                        anchors.leftMargin: UM.Theme.getSize("default_margin").width
                        text: button.text
                        font: UM.Theme.getFont("default_bold")
                    }
                }

                onClicked:
                {
                    if (base.currentSections.has(section))
                    {
                        base.currentSections.delete(section);
                    }
                    else
                    {
                        base.currentSections.add(section);
                        base.updateCurrentItemUponSectionChange(section);
                    }
                    // Trigger update on base.currentSections
                    base.currentSections = base.currentSections;
                }
            }

            delegate: Cura.RadioButton
            {
                id: radioButton
                anchors
                {
                    left: parent !== null ? parent.left : undefined
                    leftMargin: UM.Theme.getSize("standard_list_lineheight").width

                    right: parent !== null ? parent.right : undefined
                    rightMargin: UM.Theme.getSize("default_margin").width
                }
                height: visible ? UM.Theme.getSize("standard_list_lineheight").height : 0 //This causes the scrollbar to vary in length due to QTBUG-76830.

                checked: machineList.currentIndex == index
                text: name
                visible: base.currentSections.has(section)
                onClicked: machineList.currentIndex = index
            }
        }

        // Vertical line
        Rectangle
        {
            id: verticalLine
            anchors.top: parent.top
            height: parent.height - UM.Theme.getSize("default_lining").height
            width: UM.Theme.getSize("default_lining").height
            color: UM.Theme.getColor("lining")
        }

        // User-editable printer name row
        Column
        {
            width: Math.floor(parent.width * 0.52)

            spacing: UM.Theme.getSize("default_margin").width
            padding: UM.Theme.getSize("default_margin").width

            UM.Label
            {
                width: parent.width - (2 * UM.Theme.getSize("default_margin").width)
                text: base.getMachineName()
                color: UM.Theme.getColor("primary_button")
                font: UM.Theme.getFont("huge")
                elide: Text.ElideRight
            }
            Grid
            {
                width: parent.width
                columns: 2
                rowSpacing: UM.Theme.getSize("default_lining").height
                columnSpacing: UM.Theme.getSize("default_margin").width

                verticalItemAlignment: Grid.AlignVCenter

                UM.Label
                {
                    id: manufacturerLabel
                    text: catalog.i18nc("@label", "Manufacturer")
                }
                UM.Label
                {
                    text: base.getMachineMetaDataEntry("manufacturer")
                    width: parent.width - manufacturerLabel.width
                    wrapMode: Text.WordWrap
                }
                UM.Label
                {
                    id: profileAuthorLabel
                    text: catalog.i18nc("@label", "Profile author")
                }
                UM.Label
                {
                    text: base.getMachineMetaDataEntry("author")
                    width: parent.width - profileAuthorLabel.width
                    wrapMode: Text.WordWrap
                }

                UM.Label
                {
                    id: printerNameLabel
                    text: catalog.i18nc("@label", "Printer name")
                }

                Cura.TextField
                {
                    id: printerNameTextField
                    placeholderText: catalog.i18nc("@text", "Please name your printer")
                    maximumLength: 40
                    width: parent.width - (printerNameLabel.width + (3 * UM.Theme.getSize("default_margin").width))
                    validator: RegularExpressionValidator
                    {
                        regularExpression: printerNameTextField.machineNameValidator.machineNameRegex
                    }
                    property var machineNameValidator: Cura.MachineNameValidator { }
                }
            }
        }
    }
}
