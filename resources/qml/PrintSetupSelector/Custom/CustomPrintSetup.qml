// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.3 as UM
import Cura 1.0 as Cura


Item
{
    id: customPrintSetup
    height: childrenRect.height + padding

    property real padding: UM.Theme.getSize("default_margin").width
    property bool multipleExtruders: extrudersModel.count > 1

    Cura.ExtrudersModel
    {
        id: extrudersModel
    }

    // Profile selector row
    GlobalProfileSelector
    {
        id: globalProfileRow
        anchors
        {
            top: parent.top
            topMargin: parent.padding
            left: parent.left
            leftMargin: parent.padding
            right: parent.right
            rightMargin: parent.padding
        }
    }

    UM.TabRow
    {
        id: tabBar

        visible: multipleExtruders  // The tab row is only visible when there are more than 1 extruder

        anchors
        {
            top: globalProfileRow.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            leftMargin: parent.padding
            right: parent.right
            rightMargin: parent.padding
        }

        currentIndex: Math.max(Cura.ExtruderManager.activeExtruderIndex, 0)

        Repeater
        {
            id: repeater
            model: extrudersModel
            delegate: UM.TabRowButton
            {
                contentItem: Item
                {
                    Cura.ExtruderIcon
                    {
                        anchors.horizontalCenter: parent.horizontalCenter
                        materialColor: model.color
                        extruderEnabled: model.enabled
                    }
                }
                onClicked:
                {
                    Cura.ExtruderManager.setActiveExtruderIndex(tabBar.currentIndex)
                }
            }
        }

        // When the model of the extruders is rebuilt, the list of extruders is briefly emptied and rebuilt.
        // This causes the currentIndex of the tab to be in an invalid position which resets it to 0.
        // Therefore we need to change it back to what it was: The active extruder index.
        Connections
        {
            target: repeater.model
            onModelChanged:
            {
                tabBar.currentIndex = Math.max(Cura.ExtruderManager.activeExtruderIndex, 0)
            }
        }
    }

    Rectangle
    {
        height: UM.Theme.getSize("print_setup_widget").height
        anchors
        {
            top: tabBar.bottom
            left: parent.left
            leftMargin: parent.padding
            right: parent.right
            rightMargin: parent.padding
            topMargin: -UM.Theme.getSize("default_lining").width
        }
        z: tabBar.z - 1
        // Don't show the border when only one extruder
        border.color: tabBar.visible ? UM.Theme.getColor("lining") : "transparent"
        border.width: UM.Theme.getSize("default_lining").width

        Cura.SettingView
        {
            anchors
            {
                fill: parent
                topMargin: UM.Theme.getSize("default_margin").height
                leftMargin: UM.Theme.getSize("default_margin").width
                // Small space for the scrollbar
                rightMargin: UM.Theme.getSize("narrow_margin").width
                // Compensate for the negative margin in the parent
                bottomMargin: UM.Theme.getSize("default_lining").width
            }
        }
    }
}
