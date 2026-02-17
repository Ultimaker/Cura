// Copyright (c) 2022 UltiMaker
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.3

import UM 1.3 as UM
import Cura 1.1 as Cura

Rectangle
{
    id: root

    property var machineManager: Cura.MachineManager
    property var activeMachine: machineManager.activeMachine
    property bool isMachineConnected: activeMachine ? activeMachine.is_connected : false

    color: isMachineConnected ? "green" : "red"

    Label {
        id: machineStatusLabel
        text: isMachineConnected ? qsTr("Connected") : qsTr("Disconnected")
        anchors.centerIn: parent
        color: "white"
    }
}