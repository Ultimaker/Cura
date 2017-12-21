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
    height: {
        if (collapsed) {
            return UM.Theme.getSize("objects_menu_size_collapsed").height;
        } else {
            return UM.Theme.getSize("objects_menu_size").height;
        }
    }
    Behavior on height { NumberAnimation { duration: 100 } }

    border.width: UM.Theme.getSize("default_lining").width
    border.color: UM.Theme.getColor("lining")

    property bool collapsed: false;

    SystemPalette { id: palette }

    Button {
        id: collapseButton
        anchors.top: parent.top
        anchors.topMargin: Math.floor(UM.Theme.getSize("default_margin").height + (UM.Theme.getSize("layerview_row").height - UM.Theme.getSize("default_margin").height) / 2)
        anchors.right: parent.right
        anchors.rightMargin: UM.Theme.getSize("default_margin").width

        width: UM.Theme.getSize("standard_arrow").width
        height: UM.Theme.getSize("standard_arrow").height

        onClicked: collapsed = !collapsed

        style: ButtonStyle
        {
            background: UM.RecolorImage
            {
                width: control.width
                height: control.height
                sourceSize.width: width
                sourceSize.height: width
                color:  UM.Theme.getColor("setting_control_text")
                source: collapsed ? UM.Theme.getIcon("arrow_top") : UM.Theme.getIcon("arrow_bottom")
            }
            label: Label{ }
        }
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
                    text: Cura.ObjectManager.getItem(index).buildPlateNumber != -1 ? Cura.ObjectManager.getItem(index).buildPlateNumber + 1 : "";
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
        visible: !collapsed
        width: parent.width - 2 * UM.Theme.getSize("default_margin").height

        anchors
        {
            top: collapseButton.bottom;
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
        visible: !collapsed
        checked: boolCheck(UM.Preferences.getValue("view/filter_current_build_plate"))
        onClicked: UM.Preferences.setValue("view/filter_current_build_plate", checked)

        text: catalog.i18nc("@option:check","See only current build plate");

        anchors
        {
            left: parent.left;
            topMargin: UM.Theme.getSize("default_margin").height;
            bottomMargin: UM.Theme.getSize("default_margin").height;
            leftMargin: UM.Theme.getSize("default_margin").height;
            bottom: buildPlateSelection.top;
        }
    }

    Component {
        id: buildPlateDelegate
        Rectangle
            {
                height: childrenRect.height
                color: Cura.BuildPlateModel.getItem(index).buildPlateNumber == Cura.BuildPlateModel.activeBuildPlate ? palette.highlight : index % 2 ? palette.base : palette.alternateBase
                width: parent.width
                Label
                {
                    id: buildPlateNameLabel
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    width: parent.width - 2 * UM.Theme.getSize("default_margin").width - 30
                    text: Cura.BuildPlateModel.getItem(index) ? Cura.BuildPlateModel.getItem(index).name : "";
                    color: Cura.BuildPlateModel.activeBuildPlate == index ? palette.highlightedText : palette.text
                    elide: Text.ElideRight
                }

                MouseArea
                {
                    anchors.fill: parent;
                    onClicked:
                    {
                        Cura.BuildPlateModel.setActiveBuildPlate(index);
                    }
                }
            }
    }

    ScrollView
    {
        id: buildPlateSelection
        frameVisible: true
        height: UM.Theme.getSize("build_plate_selection_size").height
        width: parent.width - 2 * UM.Theme.getSize("default_margin").height

        anchors
        {
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
            model: Cura.BuildPlateModel
            width: parent.width
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
