// Copyright (c) 2019 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.10
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura


//
// This is the scroll view widget for adding a (local) printer. This scroll view shows a list view with printers
// categorized into 3 categories: "Ultimaker", "Custom", and "Other".
//
Item
{
    id: base
    height: childrenRect.height

    // The currently selected machine item in the local machine list.
    property var currentItem: (machineList.currentIndex >= 0)
                              ? machineList.model.getItem(machineList.currentIndex)
                              : null
    // The currently active (expanded) section/category, where section/category is the grouping of local machine items.
    property string currentSection: "Ultimaker B.V."
    // By default (when this list shows up) we always expand the "Ultimaker" section.
    property var preferredCategories: {
        "Ultimaker B.V.": -2,
        "Custom": -1
    }

    property int maxItemCountAtOnce: 11  // show at max 11 items at once, otherwise you need to scroll.

    // User-editable printer name
    property alias printerName: printerNameTextField.text
    property alias isPrinterNameValid: printerNameTextField.acceptableInput

    onCurrentItemChanged:
    {
        printerName = currentItem == null ? "" : currentItem.name
    }

    function updateCurrentItemUponSectionChange()
    {
        // Find the first machine from this section
        for (var i = 0; i < machineList.count; i++)
        {
            var item = machineList.model.getItem(i)
            if (item.section == base.currentSection)
            {
                machineList.currentIndex = i
                break
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
        updateCurrentItemUponSectionChange()
    }

    Row
    {
        id: localPrinterSelectionItem
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: childrenRect.height

        // ScrollView + ListView for selecting a local printer to add
        Cura.ScrollView
        {
            id: scrollView

            height: childrenHeight
            width: Math.floor(parent.width * 0.4)

            ListView
            {
                id: machineList

                // CURA-6793
                // Enabling the buffer seems to cause the blank items issue. When buffer is enabled, if the ListView's
                // individual item has a dynamic change on its visibility, the ListView doesn't redraw itself.
                // The default value of cacheBuffer is platform-dependent, so we explicitly disable it here.
                cacheBuffer: 0
                boundsBehavior: Flickable.StopAtBounds
                flickDeceleration: 20000  // To prevent the flicking behavior.
                model: UM.DefinitionContainersModel
                {
                    id: machineDefinitionsModel
                    filter: { "visible": true }
                    sectionProperty: "manufacturer"
                    preferredSections: preferredCategories
                }

                section.property: "section"
                section.delegate: sectionHeader
                delegate: machineButton
            }

            Component
            {
                id: sectionHeader

                Button
                {
                    id: button
                    width: ListView.view.width
                    height: UM.Theme.getSize("action_button").height
                    text: section

                    property bool isActive: base.currentSection == section

                    background: Rectangle
                    {
                        anchors.fill: parent
                        color: isActive ? UM.Theme.getColor("setting_control_highlight") : "transparent"
                    }

                    contentItem: Item
                    {
                        width: childrenRect.width
                        height: UM.Theme.getSize("action_button").height

                        UM.RecolorImage
                        {
                            id: arrow
                            anchors.left: parent.left
                            width: UM.Theme.getSize("standard_arrow").width
                            height: UM.Theme.getSize("standard_arrow").height
                            sourceSize.width: width
                            sourceSize.height: height
                            color: UM.Theme.getColor("text")
                            source: base.currentSection == section ? UM.Theme.getIcon("arrow_bottom") : UM.Theme.getIcon("arrow_right")
                        }

                        Label
                        {
                            id: label
                            anchors.left: arrow.right
                            anchors.leftMargin: UM.Theme.getSize("default_margin").width
                            verticalAlignment: Text.AlignVCenter
                            text: button.text
                            font: UM.Theme.getFont("default_bold")
                            color: UM.Theme.getColor("text")
                            renderType: Text.NativeRendering
                        }
                    }

                    onClicked:
                    {
                        base.currentSection = section
                        base.updateCurrentItemUponSectionChange()
                    }
                }
            }

            Component
            {
                id: machineButton

                Cura.RadioButton
                {
                    id: radioButton
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("standard_list_lineheight").width
                    anchors.right: parent.right
                    anchors.rightMargin: UM.Theme.getSize("default_margin").width
                    height: visible ? UM.Theme.getSize("standard_list_lineheight").height : 0

                    checked: ListView.view.currentIndex == index
                    text: name
                    visible: base.currentSection == section
                    onClicked: ListView.view.currentIndex = index
                }
            }
        }

        // Vertical line
        Rectangle
        {
            id: verticalLine
            anchors.top: parent.top
            height: childrenHeight - UM.Theme.getSize("default_lining").height
            width: UM.Theme.getSize("default_lining").height
            color: UM.Theme.getColor("lining")
        }

        // User-editable printer name row
        Column
        {
            width: Math.floor(parent.width * 0.6)

            spacing: UM.Theme.getSize("default_margin").width
            padding: UM.Theme.getSize("default_margin").width

            Label
            {
                width: parent.width
                wrapMode: Text.WordWrap
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

                Label
                {
                    text: catalog.i18nc("@label", "Manufacturer")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering
                }
                Label
                {
                    text: base.getMachineMetaDataEntry("manufacturer")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering
                }
                Label
                {
                    text: catalog.i18nc("@label", "Author")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering
                }
                Label
                {
                    text: base.getMachineMetaDataEntry("author")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering
                }

                Label
                {
                    text: catalog.i18nc("@label", "Printer name")
                    font: UM.Theme.getFont("default")
                    color: UM.Theme.getColor("text")
                    renderType: Text.NativeRendering
                }

                Cura.TextField
                {
                    id: printerNameTextField
                    placeholderText: catalog.i18nc("@text", "Please give your printer a name")
                    maximumLength: 40
                    validator: RegExpValidator
                    {
                        regExp: printerNameTextField.machineNameValidator.machineNameRegex
                    }
                    property var machineNameValidator: Cura.MachineNameValidator { }
                }
            }
        }


    }
}
