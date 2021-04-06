// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

import QtQuick 2.7
import QtQuick.Controls 2.1
import QtQuick.Window 2.2

import UM 1.3 as UM
import Cura 1.1 as Cura


UM.Dialog  {
    id: dynamical3DPauseDialog

    color: UM.Theme.getColor("main_background")

    flags: Qt.Dialog |  Qt.WindowCloseButtonHint;
    minimumWidth: 500 * screenScaleFactor
    minimumHeight: 650 * screenScaleFactor
    width: minimumWidth
    height: minimumHeight

    // background: Rectangle {
        
    // }
    
    Rectangle{
        id: header
        width: parent.width + 2 * margin // margin from Dialog.qml
        height: childrenRect.height + topPadding

        anchors.top: parent.top
        anchors.topMargin: -margin
        anchors.horizontalCenter: parent.horizontalCenter

        property real topPadding: UM.Theme.getSize("wide_margin").height

        color: UM.Theme.getColor("main_background")
 
    }

    PausesPage {
        id: pausesPage
       
        anchors.centerIn: parent
        function cerrar() {
            Window.window.close()
        }
    }
    rightButtons: Cura.PrimaryButton
    {
        //: Close about dialog button
        id: closeButton
        UM.I18nCatalog{id: catalog; name: "cura"}
        text: catalog.i18nc("@action:button","Aceptar");

        onClicked: dynamical3DPauseDialog.visible = false;
    }


}