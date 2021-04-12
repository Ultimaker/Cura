

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Layouts 1.3



import UM 1.3 as UM
import Cura 1.1 as Cura



Item {
    id: pausesPage
    anchors.fill: parent
    anchors.margins: UM.Theme.getSize("wide_margin").width

    ColumnLayout {
        spacing: UM.Theme.getSize("wide_margin").height
        width: parent.width
        anchors.fill: parent

        Label {
            id: backupTitle
            text: "Puntos de pausa"
            font: UM.Theme.getFont("large")
            color: UM.Theme.getColor("text")
            //color: UM.Theme.getColor("main_background")

            Layout.fillWidth: true
            renderType: Text.NativeRendering
            background: Rectangle {
                color: UM.Theme.getColor("main_background")
            }
        }

        Label
        {
            text: "No hay pausas establecidas. Utiliza el botón 'Añadir pausa' para crear una."
            width: parent.width
            font: UM.Theme.getFont("default")
            color: UM.Theme.getColor("text")
            wrapMode: Label.WordWrap
            visible: pauseList.model.length == 0
            Layout.fillWidth: true
            Layout.fillHeight: true
            renderType: Text.NativeRendering
        }

        PauseList {
            id: pauseList
            model: Dynamical3DPause.points
            Layout.fillWidth: true
            Layout.fillHeight: true
        }

        

        // PausesListFooter {
        //     id: pausesListFooter
        //     width: parent.width
            
        // }
        function cerrar() {
            parent.cerrar()
        }
    }

}
