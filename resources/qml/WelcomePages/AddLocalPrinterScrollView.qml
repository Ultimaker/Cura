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
    property bool hasSearchFilter: false
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
        printerName = currentItem && currentItem.name? currentItem.name: ""
    }

    function updateCurrentItemUponSectionChange(section)
    {
        // Find the first machine from this section
        for (var i = 0; i < machineList.count; i ++)
        {
            const item = machineList.model.getItem(i);
            if (item.section == section)
            {
                updateCurrentItem(i)
                break;
            }
        }
    }

    function updateCurrentItem(index)
    {
        machineList.currentIndex = index;
        currentItem = machineList.model.getItem(index);
        if (currentItem && currentItem.name)
        {
            machineName.text = currentItem.name
            manufacturer.text = currentItem.metadata["manufacturer"]
            author.text = currentItem.metadata["author"]
        }
        else
        {
            machineName.text = "No printers Found"
            manufacturer.text = ""
            author.text = ""
        }
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

        Column
        {
            id: root
            width: Math.floor(parent.width * 0.48)
            height: parent.height
            Item
            {
                width: root.width
                height: filter.height
                Cura.TextField
                {
                    id: filter
                    width: parent.width
                    implicitHeight: parent.height
                    background: Rectangle {
                        id: background
                        color: UM.Theme.getColor("main_background")
                        radius: UM.Theme.getSize("default_radius").width
                        border.color: UM.Theme.getColor("primary_button")
                    }
                    height: UM.Theme.getSize("small_button_icon").height * 2
                    placeholderText: catalog.i18nc("@label:textbox", "Search Printer")
                    placeholderTextColor: UM.Theme.getColor("primary_button")
                    font: UM.Theme.getFont("medium_italic")
                    leftPadding: searchIcon.width + UM.Theme.getSize("default_margin").width * 2

                    UM.ColorImage
                    {
                        id: searchIcon
                        source: UM.Theme.getIcon("Magnifier")
                        anchors
                        {
                            verticalCenter: parent.verticalCenter
                            left: parent.left
                            leftMargin: UM.Theme.getSize("default_margin").width
                        }
                        height: UM.Theme.getSize("small_button_icon").height
                        width: height
                        color: UM.Theme.getColor("text")
                    }

                    onTextChanged: editingFinished()
                    onEditingFinished:
                    {
                        machineDefinitionsModel.filter = {"name" : "*" + text.toLowerCase() + "*", "visible": true}
                        base.hasSearchFilter = (text.length > 0)
                        updateDefinitionModel()
                    }

                    Keys.onEscapePressed: filter.text = ""
                    function updateDefinitionModel()
                    {
                        if (base.hasSearchFilter)
                        {
                            base.currentSections.clear()
                            for (var i = 0; i < machineDefinitionsModel.count; i++)
                            {
                                var sectionexpanded = machineDefinitionsModel.getItem(i)["section"]
                                if (!base.currentSections.has(sectionexpanded))
                                {
                                    base.currentSections.add(sectionexpanded);
                                }
                            }
                            base.updateCurrentItem(0)

                            // Trigger update on base.currentSections
                            base.currentSections = base.currentSections;
                        }
                        else
                        {
                            const initialSection = "Ultimaker B.V.";
                            base.currentSections.clear();
                            base.currentSections.add(initialSection);
                            updateCurrentItemUponSectionChange(initialSection);
                            updateCurrentItem(0)
                            // Trigger update on base.currentSections
                            base.currentSections = base.currentSections;
                        }

                    }
                }

                UM.SimpleButton
                {
                    id: clearFilterButton
                    iconSource: UM.Theme.getIcon("Cancel")
                    visible: base.hasSearchFilter

                    height: Math.round(filter.height * 0.5)
                    width: visible ? height : 0

                    anchors.verticalCenter: filter.verticalCenter
                    anchors.right: filter.right
                    anchors.rightMargin: UM.Theme.getSize("default_margin").width

                    color: UM.Theme.getColor("setting_control_button")
                    hoverColor: UM.Theme.getColor("setting_control_button_hover")

                    onClicked:
                    {
                        filter.text = ""
                        filter.forceActiveFocus()
                    }
                }
            }

            //Selecting a local printer to add from this list.
            ListView
            {
                id: machineList
                width: root.width
                height: root.height - filter.height
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
                    onClicked: base.updateCurrentItem(index)
                }
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
                id: machineName
                width: parent.width - (2 * UM.Theme.getSize("default_margin").width)
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
                    id: manufacturer
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
                    id: author
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
