import QtQuick 2.10
import QtQuick.Controls 2.0
import UM 1.5 as UM
import Cura 1.1 as Cura

Rectangle
{
    id: viewportOverlay

    property var machineManager: Cura.MachineManager
    property var activeMachine: machineManager.activeMachine
    property bool isMachineConnected: activeMachine ? activeMachine.is_connected : false

    color: "black"
    anchors.fill: parent

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Text
    {
        anchors.centerIn: parent
        text: "Hello World"
        font.pointSize: 24
        color: "white"
    }
}