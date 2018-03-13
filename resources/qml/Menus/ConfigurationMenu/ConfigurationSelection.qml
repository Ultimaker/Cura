// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.0
import QtQuick.Controls.Styles 1.4

import UM 1.2 as UM
import Cura 1.0 as Cura

Item
{
    id: configurationSelector
    property var connectedDevice: Cura.MachineManager.printerOutputDevices.length >= 1 ? Cura.MachineManager.printerOutputDevices[0] : null
    property var panelWidth: control.width
    property var panelVisible: false

    SyncButton {
        onClicked: configurationSelector.state == "open" ? configurationSelector.state = "closed" : configurationSelector.state = "open"
        outputDevice: connectedDevice
    }

    Popup {
        id: popup
        clip: true
        y: configurationSelector.height - UM.Theme.getSize("default_lining").height
        x: configurationSelector.width - width
        width: panelWidth
        visible: panelVisible && connectedDevice != null
        padding: UM.Theme.getSize("default_lining").width
        contentItem: ConfigurationListView {
            id: configList
            width: panelWidth - 2 * popup.padding
            outputDevice: connectedDevice
        }
        background: Rectangle {
            color: UM.Theme.getColor("setting_control")
            border.color: UM.Theme.getColor("setting_control_border")
        }
    }

    states: [
        // This adds a second state to the container where the rectangle is farther to the right
        State {
            name: "open"
            PropertyChanges {
                target: popup
                height: configList.computedHeight
            }
        },
        State {
            name: "closed"
            PropertyChanges {
                target: popup
                height: 0
            }
        }
    ]
    transitions: [
        // This adds a transition that defaults to applying to all state changes
        Transition {
            // This applies a default NumberAnimation to any changes a state change makes to x or y properties
            NumberAnimation { properties: "height"; duration: 200; easing.type: Easing.InOutQuad; }
        }
    ]
}