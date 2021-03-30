// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2

import UM 1.3 as UM
import Cura 1.0 as Cura



RowLayout {
    id: pausesListFooter
    width: parent.width


    Cura.PrimaryButton {
        id: addPauseButton
        text: "Añadir Pausa"
        iconSource: UM.Theme.getIcon("plus")
        onClicked: alturaDialog.open()
        // busy: CuraDrive.isCreatingBackup
    }

    Dialog {
        id: alturaDialog
        modality: Qt.ApplicationModal

        title: "Altura"

        signal reset()
        onReset: {
            alturaField.value = 1;
            copiesField.focus = true;
        }

        onAccepted: Dynamical3DPause.addPoint(alturaField.value)

        onVisibleChanged: {
            alturaField.forceActiveFocus();
        }

        standardButtons: StandardButton.Ok | StandardButton.Cancel

        Row {
            spacing: UM.Theme.getSize("default_margin").width

            Label {
                text: "Establece el punto de pausa"
                anchors.verticalCenter: alturaField.verticalCenter
            }

            SpinBox {
                id: alturaField
                focus: true
                minimumValue: 1
                maximumValue: (UM.SimulationView.numLayers <1 ) ? 100 :  UM.SimulationView.numLayers
            }
        }
    }
}
