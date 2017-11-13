// Copyright (c) 2017 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.1
import QtQuick.Controls.Styles 1.1
import QtQuick.Layouts 1.1
import QtQuick.Dialogs 1.1

import UM 1.3 as UM
import Cura 1.2 as Cura

import "Menus"

Rectangle
{
    id: base;

    color: UM.Theme.getColor("tool_panel_background")

    width: UM.Theme.getSize("objects_menu_size").width
    height: UM.Theme.getSize("objects_menu_size").height

    SystemPalette { id: palette }

    Button
    {
        id: openFileButton;
        text: catalog.i18nc("@action:button","Open File");
        iconSource: UM.Theme.getIcon("load")
        style: UM.Theme.styles.tool_button
        tooltip: '';
        anchors
        {
            top: parent.top;
            topMargin: UM.Theme.getSize("default_margin").height;
            left: parent.left;
            leftMargin: UM.Theme.getSize("default_margin").height;
        }
        action: Cura.Actions.open;
    }

    Component {
        id: objectDelegate
        Rectangle
            {
                height: childrenRect.height
                color: Cura.ObjectManager.getItem(index).isSelected ? palette.highlight : index % 2 ? palette.base : palette.alternateBase
                width: parent.width
                Label
                {
                    id: nodeNameLabel
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    //anchors.right: parent.right
                    width: parent.width - 2 * UM.Theme.getSize("default_margin").width - 30
                    text: Cura.ObjectManager.getItem(index) ? Cura.ObjectManager.getItem(index).name : "";
                    color: Cura.ObjectManager.getItem(index).isSelected ? palette.highlightedText : (Cura.ObjectManager.getItem(index).isOutsideBuildArea ? palette.mid : palette.text)
                    elide: Text.ElideRight
                }

                Label
                {
                    id: buildPlateNumberLabel
                    width: 20
                    anchors.left: nodeNameLabel.right
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    anchors.right: parent.right
                    text: Cura.ObjectManager.getItem(index) ? Cura.ObjectManager.getItem(index).buildPlateNumber : 0;
                    color: Cura.ObjectManager.getItem(index).isSelected ? palette.highlightedText : palette.text
                    elide: Text.ElideRight
                }

                MouseArea
                {
                    anchors.fill: parent;
                    onClicked:
                    {
                        Cura.ObjectManager.changeSelection(index);
                    }
                }
            }
    }

    // list all the scene nodes
    ScrollView
    {
        id: objectsList
        frameVisible: true
        width: parent.width - 2 * UM.Theme.getSize("default_margin").height

        anchors
        {
            top: openFileButton.bottom;
            topMargin: UM.Theme.getSize("default_margin").height;
            left: parent.left;
            leftMargin: UM.Theme.getSize("default_margin").height;
            bottom: filterBuildPlateCheckbox.top;
            bottomMargin: UM.Theme.getSize("default_margin").height;
        }

        Rectangle
        {
            parent: viewport
            anchors.fill: parent
            color: palette.light
        }

        ListView
        {
            id: listview
            model: Cura.ObjectManager
            width: parent.width
            delegate: objectDelegate
        }
    }


    CheckBox
    {
        id: filterBuildPlateCheckbox
        checked: boolCheck(UM.Preferences.getValue("view/filter_current_build_plate"))
        onClicked: UM.Preferences.setValue("view/filter_current_build_plate", checked)

        text: catalog.i18nc("@option:check","Filter active build plate");

        anchors
        {
            left: parent.left;
            topMargin: UM.Theme.getSize("default_margin").height;
            bottomMargin: UM.Theme.getSize("default_margin").height;
            leftMargin: UM.Theme.getSize("default_margin").height;
            bottom: buildPlateSelection.top;
        }
    }

    ListModel
    {
        id: buildPlatesModel

        ListElement
        {
            name: "build plate 0"
            buildPlateNumber: 0
        }
        ListElement
        {
            name: "build plate 1"
            buildPlateNumber: 1
        }
        ListElement
        {
            name: "build plate 2"
            buildPlateNumber: 2
        }
    }

    Component {
        id: buildPlateDelegate
        Rectangle
            {
                height: childrenRect.height
                color: CuraApplication.activeBuildPlate == buildPlateNumber ? palette.highlight : index % 2 ? palette.base : palette.alternateBase
                width: parent.width
                Label
                {
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    anchors.right: parent.right
                    text: name //Cura.ObjectManager.getItem(index).name;
                    color: CuraApplication.activeBuildPlate == buildPlateNumber ? palette.highlightedText : palette.text
                    elide: Text.ElideRight
                }

                MouseArea
                {
                    anchors.fill: parent;
                    onClicked:
                    {
                        CuraApplication.setActiveBuildPlate(buildPlateNumber);
                    }
                }
            }
    }

    ScrollView
    {
        id: buildPlateSelection
        frameVisible: true
        height: 100
        width: parent.width - 2 * UM.Theme.getSize("default_margin").height

        anchors
        {
            // top: objectsList.bottom;
            topMargin: UM.Theme.getSize("default_margin").height;
            left: parent.left;
            leftMargin: UM.Theme.getSize("default_margin").height;
            bottom: arrangeAllBuildPlatesButton.top;
            bottomMargin: UM.Theme.getSize("default_margin").height;
        }

        Rectangle
        {
            parent: viewport
            anchors.fill: parent
            color: palette.light
        }

        ListView
        {
            id: buildPlateListView
            model: buildPlatesModel

            onModelChanged:
            {
                //currentIndex = -1;
            }
            width: parent.width
            currentIndex: -1
            onCurrentIndexChanged:
            {
                //base.selectedPrinter = listview.model[currentIndex];
                // Only allow connecting if the printer has responded to API query since the last refresh
                //base.completeProperties = base.selectedPrinter != null && base.selectedPrinter.getProperty("incomplete") != "true";
            }
            //Component.onCompleted: manager.startDiscovery()
            delegate: buildPlateDelegate
        }
    }

    Button
    {
        id: arrangeAllBuildPlatesButton;
        text: catalog.i18nc("@action:button","Arrange to all build plates");
        //iconSource: UM.Theme.getIcon("load")
        //style: UM.Theme.styles.tool_button
        height: 25
        tooltip: '';
        anchors
        {
            //top: buildPlateSelection.bottom;
            topMargin: UM.Theme.getSize("default_margin").height;
            left: parent.left;
            leftMargin: UM.Theme.getSize("default_margin").height;
            right: parent.right;
            rightMargin: UM.Theme.getSize("default_margin").height;
            bottom: arrangeBuildPlateButton.top;
            bottomMargin: UM.Theme.getSize("default_margin").height;
        }
        action: Cura.Actions.arrangeAllBuildPlates;
    }

    Button
    {
        id: arrangeBuildPlateButton;
        text: catalog.i18nc("@action:button","Arrange current build plate");
        height: 25
        tooltip: '';
        anchors
        {
            topMargin: UM.Theme.getSize("default_margin").height;
            left: parent.left;
            leftMargin: UM.Theme.getSize("default_margin").height;
            right: parent.right;
            rightMargin: UM.Theme.getSize("default_margin").height;
            bottom: parent.bottom;
            bottomMargin: UM.Theme.getSize("default_margin").height;
        }
        action: Cura.Actions.arrangeAll;
    }


}
