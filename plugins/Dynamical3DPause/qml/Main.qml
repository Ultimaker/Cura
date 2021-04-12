

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.3

import UM 1.3 as UM
import Cura 1.1 as Cura


UM.Dialog  {
    id: dynamical3DPauseDialog

    color: UM.Theme.getColor("main_background")

    flags: Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint | Qt.FramelessWindowHint;
    minimumWidth: 400 * screenScaleFactor
    minimumHeight: 450 * screenScaleFactor
    width: minimumWidth
    height: minimumHeight

    backgroundColor: UM.Theme.getColor("main_background")
    

    PausesPage {
        id: pausesPage
       
        anchors.centerIn: parent
        function cerrar() {
            Window.window.close()
        }
    }



    rightButtons: Cura.PrimaryButton {
        id: closeButton
        UM.I18nCatalog{id: catalog; name: "cura"}
        text: catalog.i18nc("@action:button","Aceptar");

        onClicked: dynamical3DPauseDialog.visible = false;
    }




    leftButtons: Cura.PrimaryButton {
        id: addPauseButton
        text: "Añadir Pausa"
        iconSource: UM.Theme.getIcon("plus")
        onClicked: alturaDialog.open()
 
    }

    AlturaDialog {
        id: alturaDialog
    }



}