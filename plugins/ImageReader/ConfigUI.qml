// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    width: 250*Screen.devicePixelRatio;
    minimumWidth: 250*Screen.devicePixelRatio;
    maximumWidth: 250*Screen.devicePixelRatio;

    height: 200*Screen.devicePixelRatio;
    minimumHeight: 200*Screen.devicePixelRatio;
    maximumHeight: 200*Screen.devicePixelRatio;

    modality: Qt.Modal

    title: catalog.i18nc("@title:window", "Convert Image...")

    GridLayout 
    {
        anchors.fill: parent;
        Layout.fillWidth: true
        columnSpacing: 16
        rowSpacing: 4
        columns: 2

        Text {
            text: catalog.i18nc("@action:label","Size (mm)")
            Layout.fillWidth:true
        }
        TextField {
            id: size
            focus: true
            validator: DoubleValidator {notation: DoubleValidator.StandardNotation; bottom: 1; top: 500;}
            text: "120"
            onTextChanged: { manager.onSizeChanged(text) }
        }

        Text {
            text: catalog.i18nc("@action:label","Base Height (mm)")
            Layout.fillWidth:true
        }
        TextField {
            id: base_height
            validator: DoubleValidator {notation: DoubleValidator.StandardNotation; bottom: 0; top: 500;}
            text: "2"
            onTextChanged: { manager.onBaseHeightChanged(text) }
        }

        Text {
            text: catalog.i18nc("@action:label","Peak Height (mm)")
            Layout.fillWidth:true
        }
        TextField {
            id: peak_height
            validator: DoubleValidator {notation: DoubleValidator.StandardNotation; bottom: 0; top: 500;}
            text: "12"
            onTextChanged: { manager.onPeakHeightChanged(text) }
        }

        Text {
            text: catalog.i18nc("@action:label","Smoothing")
            Layout.fillWidth:true
        }
        Rectangle {
            width: 100
            height: 20
            color: "transparent"

            Slider {
                id: smoothing
                maximumValue: 100.0
                stepSize: 1.0
                value: 1
                width: 100
                onValueChanged: { manager.onSmoothingChanged(value) }
            }
        }

        UM.I18nCatalog{id: catalog; name:"ultimaker"}
    }

    rightButtons: [
        Button
        {
            id:ok_button
            text: catalog.i18nc("@action:button","OK");
            onClicked: { manager.onOkButtonClicked() }
            enabled: true
        },
        Button
        {
            id:cancel_button
            text: catalog.i18nc("@action:button","Cancel");
            onClicked: { manager.onCancelButtonClicked() }
            enabled: true
        }
    ]
}
