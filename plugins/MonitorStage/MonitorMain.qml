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

    color: "#FAFAFA"
    anchors.fill: parent

    UM.I18nCatalog
    {
        id: catalog
        name: "cura"
    }

    Column
    {
        anchors.centerIn: parent
        spacing: 10

        // Graph Placeholder
        Rectangle
        {
            width: 400
            height: 200
            color: "gray"
            Text
            {
                anchors.centerIn: parent
                text: "Graph Placeholder"
                color: "white"
                font.pointSize: 18
            }
        }

        // Command Buttons
        Column
        {
            spacing: 5
            Text { text: "Command Buttons"; color: "white"; font.pointSize: 16 }
            Row {
                spacing: 5
                Button { text: "Z+" }
                Button { text: "Z-" }
            }
            Row {
                spacing: 5
                Button { text: "X+" }
                Button { text: "X-" }
            }
            Row {
                spacing: 5
                Button { text: "Y+" }
                Button { text: "Y-" }
            }
        }

        // Run Buttons
        Row
        {
            spacing: 10
            Text { text: "Printer Control"; color: "white"; font.pointSize: 16 }
            Button { text: "Start Printer" }
            Button { text: "Stop Printer" }
        }
    }
}