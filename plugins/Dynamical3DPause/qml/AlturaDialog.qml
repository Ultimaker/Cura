import QtQuick 2.7
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.3
import QtQuick.Dialogs 1.2


import UM 1.3 as UM
import Cura 1.1 as Cura


Item {

    function open() {
        alturaDialog.visible = true;
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

        onAccepted: {
    
            // Dynamical3DPause.addPoint(alturaField.valueFromText(alturaField.text, alturaField.locale))
            row.focus;
             Dynamical3DPause.addPoint(alturaField.value);
        }

        signal valueModified()
        onValueModified: {
           
            //labelField.text = alturaField.value
        }

        onVisibleChanged: {
            alturaField.forceActiveFocus();
        }

        standardButtons: StandardButton.Ok | StandardButton.Cancel

        Row {
            id: row
            spacing: UM.Theme.getSize("default_margin").width

            Label {
                id: labelField
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

