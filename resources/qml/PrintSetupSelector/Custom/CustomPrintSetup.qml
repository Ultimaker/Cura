// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0

import UM 1.3 as UM
import Cura 1.0 as Cura


Item
{
    id: customPrintSetup

    // TODO: Hardcoded now but UX has to decide about the height of this item
    height: 480

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

    Cura.SettingView
    {
        anchors
        {
            top: tabBar.visible ? tabBar.bottom : globalProfileRow.bottom
            topMargin: UM.Theme.getSize("default_margin").height
            left: parent.left
            leftMargin: parent.padding
            right: parent.right
            rightMargin: parent.padding
            bottom: parent.bottom
        }
    }
}
