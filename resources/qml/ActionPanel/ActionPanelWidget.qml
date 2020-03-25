// Copyright (c) 2020 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3

import UM 1.2 as UM
import Cura 1.0 as Cura


// This element hold all the elements needed for the user to trigger the slicing process, and later
// to get information about the printing times, material consumption and the output process (such as
// saving to a file, printing over network, ...
Item
{
    id: base
    height: childrenRect.height
    visible: CuraApplication.platformActivity

    property bool hasPreviewButton: true

    Rectangle
    {
        id: actionPanelWidget

        width: UM.Theme.getSize("action_panel_widget").width
        height: childrenRect.height + 2 * UM.Theme.getSize("thick_margin").height
        anchors.right: parent.right
        color: UM.Theme.getColor("main_background")
        border.width: UM.Theme.getSize("default_lining").width
        border.color: UM.Theme.getColor("lining")
        radius: UM.Theme.getSize("default_radius").width
        z: 10

        property bool outputAvailable: UM.Backend.state == UM.Backend.Done || UM.Backend.state == UM.Backend.Disabled

        Loader
        {
            id: loader
            anchors
            {
                top: parent.top
                topMargin: UM.Theme.getSize("thick_margin").height
                left: parent.left
                leftMargin: UM.Theme.getSize("thick_margin").width
                right: parent.right
                rightMargin: UM.Theme.getSize("thick_margin").width
            }
            sourceComponent: actionPanelWidget.outputAvailable ? outputProcessWidget : sliceProcessWidget
            onLoaded:
            {
                if(actionPanelWidget.outputAvailable)
                {
                    loader.item.hasPreviewButton = base.hasPreviewButton;
                }
            }
        }

        Component
        {
            id: sliceProcessWidget
            SliceProcessWidget { }
        }

        Component
        {
            id: outputProcessWidget
            OutputProcessWidget { }
        }
    }

    Item
    {
        id: additionalComponents
        width: childrenRect.width
        anchors.right: actionPanelWidget.left
        anchors.rightMargin: UM.Theme.getSize("default_margin").width
        anchors.bottom: actionPanelWidget.bottom
        anchors.bottomMargin: UM.Theme.getSize("thick_margin").height * 2
        visible: actionPanelWidget.visible
        Row
        {
            id: additionalComponentsRow
            anchors.verticalCenter: parent.verticalCenter
            spacing: UM.Theme.getSize("default_margin").width
        }
    }

    Component.onCompleted: base.addAdditionalComponents()

    Connections
    {
        target: CuraApplication
        onAdditionalComponentsChanged: base.addAdditionalComponents()
    }

    function addAdditionalComponents()
    {
        for (var component in CuraApplication.additionalComponents["saveButton"])
        {
            CuraApplication.additionalComponents["saveButton"][component].parent = additionalComponentsRow
        }
    }
}
