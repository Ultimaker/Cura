// Copyright (c) 2015 Ultimaker B.V.
// Cura is released under the terms of the AGPLv3 or higher.

import QtQuick 2.1
import QtQuick.Controls 1.1
import QtQuick.Layouts 1.1
import QtQuick.Window 2.1

import UM 1.1 as UM

UM.Dialog
{
    width: 350 * Screen.devicePixelRatio;
    minimumWidth: 350 * Screen.devicePixelRatio;
    maximumWidth: 350 * Screen.devicePixelRatio;

    height: 250 * Screen.devicePixelRatio;
    minimumHeight: 250 * Screen.devicePixelRatio;
    maximumHeight: 250 * Screen.devicePixelRatio;

    title: catalog.i18nc("@title:window", "Convert Image...")

    GridLayout 
    {
        UM.I18nCatalog{id: catalog; name:"cura"}
        anchors.fill: parent;
        Layout.fillWidth: true
        columnSpacing: 16
        rowSpacing: 4
        columns: 1

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The maximum distance of each pixel from \"Base.\"")
            Row {
                width: parent.width

                Text {
                    text: catalog.i18nc("@action:label","Height (mm)")
                    width: 150
                    anchors.verticalCenter: parent.verticalCenter
                }

                TextField {
                    id: peak_height
                    objectName: "Peak_Height"
                    validator: DoubleValidator {notation: DoubleValidator.StandardNotation; bottom: -500; top: 500;}
                    width: 180
                    onTextChanged: { manager.onPeakHeightChanged(text) }
                }
            }
        }

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The base height from the build plate in millimeters.")
            Row {
                width: parent.width

                Text {
                    text: catalog.i18nc("@action:label","Base (mm)")
                    width: 150
                    anchors.verticalCenter: parent.verticalCenter
                }

                TextField {
                    id: base_height
                    objectName: "Base_Height"
                    validator: DoubleValidator {notation: DoubleValidator.StandardNotation; bottom: 0; top: 500;}
                    width: 180
                    onTextChanged: { manager.onBaseHeightChanged(text) }
                }
            }
        }
        
        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The width in millimeters on the build plate.")
            Row {
                width: parent.width

                Text {
                    text: catalog.i18nc("@action:label","Width (mm)")
                    width: 150
                    anchors.verticalCenter: parent.verticalCenter
                }

                TextField {
                    id: width
                    objectName: "Width"
                    focus: true
                    validator: DoubleValidator {notation: DoubleValidator.StandardNotation; bottom: 1; top: 500;}
                    width: 180
                    onTextChanged: { manager.onWidthChanged(text) }
                }
            }
        }
        
        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The depth in millimeters on the build plate")
            Row {
                width: parent.width

                Text {
                    text: catalog.i18nc("@action:label","Depth (mm)")
                    width: 150
                    anchors.verticalCenter: parent.verticalCenter
                }
                TextField {
                    id: depth
                    objectName: "Depth"
                    focus: true
                    validator: DoubleValidator {notation: DoubleValidator.StandardNotation; bottom: 1; top: 500;}
                    width: 180
                    onTextChanged: { manager.onDepthChanged(text) }
                }
            }
        }
        
        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","By default, white pixels represent high points on the mesh and black pixels represent low points on the mesh. Change this option to reverse the behavior such that black pixels represent high points on the mesh and white pixels represent low points on the mesh.")
            Row {
                width: parent.width

                //Empty label so 2 column layout works.
                Text {
                    text: ""
                    width: 150
                    anchors.verticalCenter: parent.verticalCenter
                }
                ComboBox {
                    id: image_color_invert
                    objectName: "Image_Color_Invert"
                    model: [ catalog.i18nc("@item:inlistbox","Lighter is higher"), catalog.i18nc("@item:inlistbox","Darker is higher") ]
                    width: 180
                    onCurrentIndexChanged: { manager.onImageColorInvertChanged(currentIndex) }
                }
            }
        }

        UM.TooltipArea {
            Layout.fillWidth:true
            height: childrenRect.height
            text: catalog.i18nc("@info:tooltip","The amount of smoothing to apply to the image.")
            Row {
                width: parent.width

                Text {
                    text: catalog.i18nc("@action:label","Smoothing")
                    width: 150
                    anchors.verticalCenter: parent.verticalCenter
                }

                Rectangle {
                    width: 180
                    height: 20
                    Layout.fillWidth:true
                    color: "transparent"

                    Slider {
                        id: smoothing
                        objectName: "Smoothing"
                        maximumValue: 100.0
                        stepSize: 1.0
                        width: 180
                        onValueChanged: { manager.onSmoothingChanged(value) }
                    }
                }
            }
        }
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
