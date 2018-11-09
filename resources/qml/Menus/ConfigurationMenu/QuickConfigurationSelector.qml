// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura


Cura.ExpandableComponent
{
    id: base
    headerItem: Item
    {
        Cura.ExtrudersModel
        {
            id: extrudersModel
        }

        ListView
        {
            // Horizontal list that shows the extruders
            id: extrudersList

            orientation: ListView.Horizontal
            anchors.fill: parent
            model: extrudersModel

            Connections
            {
                target: Cura.MachineManager
                onGlobalContainerChanged: forceActiveFocus() // Changing focus applies the currently-being-typed values so it can change the displayed setting values.
            }

            delegate: Item
            {
                height: parent.height
                width: Math.round(ListView.view.width / extrudersModel.rowCount())

                Cura.ExtruderIcon
                {
                    id: extruderIcon
                    materialColor: model.color
                    height: parent.height
                    width: height
                }

                Label
                {
                    id: brandNameLabel

                    text: model.material_brand
                    elide: Text.ElideRight

                    anchors
                    {
                        left: extruderIcon.right
                        leftMargin: UM.Theme.getSize("default_margin").width
                        right: parent.right
                        rightMargin: UM.Theme.getSize("default_margin").width
                    }
                }
                Label
                {
                    text: model.color_name
                    elide: Text.ElideRight

                    anchors
                    {
                        left: extruderIcon.right
                        leftMargin: UM.Theme.getSize("default_margin").width
                        right: parent.right
                        rightMargin: UM.Theme.getSize("default_margin").width
                        top: brandNameLabel.bottom
                    }
                }
            }
        }
    }

    
}

/*Item
{
    id: configurationSelector
    property var connectedDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null
    property var panelWidth: control.width

    // Make this component only visible when it's a network printer and it is connected
    visible: Cura.MachineManager.activeMachineNetworkKey != "" && Cura.MachineManager.printerConnected

    function switchPopupState()
    {
        popup.visible ? popup.close() : popup.open()
    }

    SyncButton
    {
        id: syncButton
        onClicked: switchPopupState()
        outputDevice: connectedDevice
    }

    Popup
    {
        // TODO Change once updating to Qt5.10 - The 'opened' property is in 5.10 but the behavior is now implemented with the visible property
        id: popup
        clip: true
        closePolicy: Popup.CloseOnPressOutsideParent
        y: configurationSelector.height - UM.Theme.getSize("default_lining").height
        x: configurationSelector.width - width
        width: panelWidth
        visible: false
        padding: UM.Theme.getSize("default_lining").width
        transformOrigin: Popup.Top
        contentItem: ConfigurationListView
        {
            id: configList
            width: panelWidth - 2 * popup.padding
            outputDevice: connectedDevice
        }
        background: Rectangle
        {
            color: UM.Theme.getColor("setting_control")
            border.color: UM.Theme.getColor("setting_control_border")
        }
        exit: Transition
        {
            // This applies a default NumberAnimation to any changes a state change makes to x or y properties
            NumberAnimation { property: "visible"; duration: 75; }
        }
        enter: Transition
        {
            // This applies a default NumberAnimation to any changes a state change makes to x or y properties
            NumberAnimation { property: "visible"; duration: 75; }
        }
        onClosed: visible = false
        onOpened: visible = true
    }
}*/